import os
import logging
import whisper
from datetime import datetime
from pathlib import Path
from aiogram import Router, types, F
from config import AUDIO_FOLDER

logger = logging.getLogger(__name__)
router = Router()

# Load Whisper model (do this once at module level)
# "base" is a good compromise between speed and accuracy.
try:
    model = whisper.load_model("base")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    model = None

@router.message(F.voice | F.audio)
async def handle_audio_message(message: types.Message):
    if not model:
        await message.answer("Error: Whisper model not loaded. Transcription is unavailable.")
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

        # Transcribe using Whisper
        logger.info(f"Transcribing {temp_file_path}...")
        result = model.transcribe(str(temp_file_path))
        transcription_text = result.get("text", "").strip()

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
