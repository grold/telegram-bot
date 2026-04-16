import os
import logging
import shutil
import subprocess
import asyncio
import time
import numpy as np
import torch
from datetime import datetime
from pathlib import Path
from aiogram import Router, types, F
from aiogram.utils.chat_action import ChatActionSender
from config import AUDIO_FOLDER

logger = logging.getLogger(__name__)
router = Router()

# Check for ffmpeg
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
if not FFMPEG_AVAILABLE:
    logger.error("ffmpeg binary not found. Audio transcription will fail. Please install ffmpeg.")

# Global cache for the Whisper components
_whisper_model = None
_whisper_processor = None
_whisper_pipe = None

WHISPER_MAX_NEW_TOKENS = 440

async def _edit_message_safe(message: types.Message, text: str):
    """Helper to safely edit message from thread-safe coroutine."""
    try:
        await message.edit_text(text)
    except Exception as e:
        # Ignore errors like 'message is not modified' or 'message to edit not found'
        if "message is not modified" not in str(e).lower():
            logger.debug(f"Streaming edit failed: {e}")

class TelegramStreamer:
    """
    Custom streamer that updates a Telegram message with partial transcription results.
    Works with both model.generate and pipeline (which may call generate multiple times).
    """
    def __init__(self, message: types.Message, processor, interval=1.5):
        self.message = message
        self.processor = processor
        self.interval = interval
        self.last_update = 0
        self.tokens = []
        self.current_chunk_text = ""
        self.accumulated_text = ""
        self.loop = asyncio.get_event_loop()

    def put(self, value):
        """
        Called by the model when new tokens are generated.
        value: can be a tensor or an int (when used with pipeline).
        """
        if isinstance(value, torch.Tensor):
            if value.ndim == 0:
                new_tokens = [value.item()]
            elif value.ndim == 1:
                new_tokens = value.tolist()
            else:
                new_tokens = value[0].tolist()
        elif isinstance(value, (int, np.integer)):
            new_tokens = [int(value)]
        else:
            try:
                new_tokens = [int(value)]
            except (TypeError, ValueError):
                return

        self.tokens.extend(new_tokens)
            
        if time.time() - self.last_update > self.interval:
            self.update_message()

    def end(self):
        """Called when generation is complete for a chunk."""
        self.update_message()
        # Accumulate text and clear tokens for next chunk
        if self.current_chunk_text.strip():
            if self.accumulated_text:
                self.accumulated_text += " " + self.current_chunk_text.strip()
            else:
                self.accumulated_text = self.current_chunk_text.strip()
        
        self.tokens = []
        self.current_chunk_text = ""

    def update_message(self):
        """Updates the Telegram message with current accumulated text."""
        if not self.tokens and not self.accumulated_text:
            return
            
        try:
            # Decode current chunk
            new_text = self.processor.decode(self.tokens, skip_special_tokens=True)
            
            self.current_chunk_text = new_text
            
            # Combine with previous chunks
            display_text = self.accumulated_text
            if self.current_chunk_text.strip():
                if display_text:
                    display_text += " " + self.current_chunk_text.strip()
                else:
                    display_text = self.current_chunk_text.strip()

            if display_text.strip() and display_text.strip() != self.message.text:
                # Use helper to ensure we pass a real coroutine object
                asyncio.run_coroutine_threadsafe(
                    _edit_message_safe(self.message, f"🎤 {display_text}..."),
                    self.loop
                )
                self.last_update = time.time()
        except Exception as e:
            logger.warning(f"Error updating streaming message: {e}")

def _get_whisper_components():
    """
    Lazy loader for Whisper model, processor, and pipeline.
    Performs heavy imports and initialization only on the first call.
    """
    global _whisper_model, _whisper_processor, _whisper_pipe
    if _whisper_pipe is not None:
        return _whisper_model, _whisper_processor, _whisper_pipe

    try:
        from transformers import AutoProcessor, pipeline
        from optimum.intel.openvino import OVModelForSpeechSeq2Seq

        MODEL_ID = "OpenVINO/whisper-base-int8-ov"
        logger.info(f"Loading Whisper model {MODEL_ID} (Lazy Load)...")
        
        processor = AutoProcessor.from_pretrained(MODEL_ID)
        
        try:
            logger.info("Attempting to load Whisper model on Intel GPU...")
            model = OVModelForSpeechSeq2Seq.from_pretrained(MODEL_ID, device="GPU")
            logger.info("Whisper model loaded successfully on Intel GPU.")
        except Exception as e:
            logger.warning(f"Failed to load Whisper model on Intel GPU: {e}. Falling back to CPU.")
            model = OVModelForSpeechSeq2Seq.from_pretrained(MODEL_ID, device="CPU")
            logger.info("Whisper model loaded successfully on CPU.")
        
        _whisper_model = model
        _whisper_processor = processor
        _whisper_pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            chunk_length_s=30,
            stride_length_s=5,
        )
        return _whisper_model, _whisper_processor, _whisper_pipe
    except Exception as e:
        logger.error(f"Failed to load Whisper components: {e}")
        return None, None, None

def load_audio(file_path: str | Path) -> np.ndarray:
    """
    Load audio file and convert to 16kHz mono PCM using ffmpeg.
    Whisper models expect 16kHz float32 mono audio.
    """
    command = [
        "ffmpeg", "-i", str(file_path),
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ar", "16000", "-ac", "1", "-"
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {stderr.decode()}")
        return np.frombuffer(stdout, dtype=np.float32)
    except Exception as e:
        logger.error(f"Error loading audio with ffmpeg: {e}")
        raise

@router.message(F.voice | F.audio)
async def handle_audio_message(message: types.Message):
    if not FFMPEG_AVAILABLE:
        await message.answer("Error: ffmpeg is not installed on the server. Transcription is unavailable.")
        return

    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        global _whisper_model, _whisper_processor, _whisper_pipe
        status_msg = None
        if _whisper_pipe is None:
            status_msg = await message.reply("⏳ Loading transcription model for the first time... this may take a moment.")
            model, processor, pipe = await asyncio.to_thread(_get_whisper_components)
        else:
            model, processor, pipe = _whisper_model, _whisper_processor, _whisper_pipe

        if not pipe or not processor:
            error_text = "Error: Whisper model could not be loaded. Transcription is unavailable."
            if status_msg:
                await status_msg.edit_text(f"❌ {error_text}")
            else:
                await message.answer(error_text)
            return

        if message.voice:
            file_id = message.voice.file_id
            file_ext = "ogg" 
        elif message.audio:
            file_id = message.audio.file_id
            file_ext = message.audio.file_name.split('.')[-1] if message.audio.file_name else "mp3"
        else:
            return

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        target_dir = AUDIO_FOLDER / date_str
        target_dir.mkdir(parents=True, exist_ok=True)

        user_part = message.from_user.username or str(message.from_user.id)
        chat_part = message.chat.title or "private"
        orig_name = "voice" if message.voice else (Path(message.audio.file_name).stem if message.audio.file_name else "audio")

        def sanitize(s):
            return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)

        temp_file_path = target_dir / f"{sanitize(user_part)}-{sanitize(chat_part)}-{sanitize(orig_name)}_{now.strftime('%H%M%S')}.{file_ext}"

        try:
            bot = message.bot
            file_info = await bot.get_file(file_id)
            await bot.download_file(file_info.file_path, destination=temp_file_path)

            logger.info(f"Transcribing {temp_file_path}...")
            
            if not status_msg:
                status_msg = await message.reply("🔄 Transcribing audio...")
            else:
                await status_msg.edit_text("🔄 Transcribing audio...")
            
            audio_data = await asyncio.to_thread(load_audio, temp_file_path)
            
            streamer = TelegramStreamer(status_msg, processor)
            
            def run_pipe():
                return pipe(
                    audio_data, 
                    generate_kwargs={"streamer": streamer, "num_beams": 1, "max_new_tokens": WHISPER_MAX_NEW_TOKENS}
                )

            result = await asyncio.to_thread(run_pipe)
            transcription_text = result['text'].strip()

            if not transcription_text:
                transcription_text = "[No speech detected]"

            txt_file_path = temp_file_path.with_suffix(".txt")
            with open(txt_file_path, "w", encoding="utf-8") as f:
                f.write(transcription_text)

            response = f"🎤 Transcription for {message.from_user.full_name}:\n\n<blockquote expandable>{transcription_text}</blockquote>"
            await message.reply(response)
            
            if status_msg:
                await status_msg.delete()

        except Exception as e:
            logger.error(f"Error processing audio message: {e}")
            error_text = f"Failed to transcribe audio: {str(e)}"
            if status_msg:
                try:
                    await status_msg.edit_text(f"❌ {error_text}")
                except Exception:
                    await message.answer(f"❌ {error_text}")
            else:
                await message.reply(error_text)
