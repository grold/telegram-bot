import os
import logging
import shutil
import subprocess
import numpy as np
from datetime import datetime
from pathlib import Path
from aiogram import Router, types, F
from transformers import AutoProcessor
from optimum.intel.openvino import OVModelForSpeechSeq2Seq
from config import AUDIO_FOLDER

logger = logging.getLogger(__name__)
router = Router()

# Check for ffmpeg
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
if not FFMPEG_AVAILABLE:
    logger.error("ffmpeg binary not found. Audio transcription will fail. Please install ffmpeg.")

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

# Load Whisper model (do this once at module level)
# Use OpenVINO optimized model for Intel Iris Graphics
MODEL_ID = "OpenVINO/whisper-base-int8-ov"
try:
    logger.info(f"Loading Whisper model {MODEL_ID} on Intel GPU...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    try:
        model = OVModelForSpeechSeq2Seq.from_pretrained(MODEL_ID, device="GPU")
        logger.info("Whisper model loaded successfully on Intel GPU.")
    except Exception as e:
        logger.warning(f"Failed to load Whisper model on Intel GPU: {e}. Falling back to CPU.")
        model = OVModelForSpeechSeq2Seq.from_pretrained(MODEL_ID, device="CPU")
        logger.info("Whisper model loaded successfully on CPU.")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    model = None
    processor = None

@router.message(F.voice | F.audio)
async def handle_audio_message(message: types.Message):
    if not model or not processor:
        await message.answer("Error: Whisper model not loaded. Transcription is unavailable.")
        return

    if not FFMPEG_AVAILABLE:
        await message.answer("Error: ffmpeg is not installed on the server. Transcription is unavailable.")
        return

    # Check if it's a voice or audio file
    if message.voice:
        file_id = message.voice.file_id
        file_ext = "ogg" # Telegram voice messages are usually .ogg (Opus)
    elif message.audio:
        file_id = message.audio.file_id
        file_ext = message.audio.file_name.split('.')[-1] if message.audio.file_name else "mp3"
    else:
        return

    # Create directory structure: audio/YYYY-MM-DD/
    date_str = datetime.now().strftime("%Y-%m-%d")
    target_dir = AUDIO_FOLDER / date_str
    target_dir.mkdir(parents=True, exist_ok=True)

    # Temporary local path for the downloaded file
    temp_file_name = f"{message.from_user.id}_{datetime.now().strftime('%H%M%S')}.{file_ext}"
    temp_file_path = target_dir / temp_file_name

    try:
        # Download the file
        bot = message.bot
        file_info = await bot.get_file(file_id)
        await bot.download_file(file_info.file_path, destination=temp_file_path)

        # Transcribe using OpenVINO Whisper
        logger.info(f"Transcribing {temp_file_path}...")
        
        # Load audio data
        audio_data = load_audio(temp_file_path)
        
        # Preprocess
        input_features = processor(audio_data, sampling_rate=16000, return_tensors="pt").input_features
        
        # Generate transcription
        predicted_ids = model.generate(input_features)
        transcription_text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()

        if not transcription_text:
            transcription_text = "[No speech detected]"

        # Save transcription to a .txt file
        txt_file_path = temp_file_path.with_suffix(".txt")
        with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write(transcription_text)

        # Send response to group
        response = f"🎤 Transcription for {message.from_user.full_name}:\n\n{transcription_text}"
        await message.reply(response)

    except Exception as e:
        logger.error(f"Error processing audio message: {e}")
        await message.reply(f"Failed to transcribe audio: {str(e)}")
