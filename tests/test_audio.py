import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, Voice, Audio, User
from handlers.audio import handle_audio_message
from pathlib import Path

@pytest.mark.asyncio
async def test_handle_voice_message():
    # Mock message and bot
    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()
    message.answer = AsyncMock()
    message.voice = MagicMock(spec=Voice)
    message.voice.file_id = "voice_file_id"
    message.audio = None
    
    # Mock from_user
    mock_user = MagicMock(spec=User)
    mock_user.id = 12345
    mock_user.full_name = "Test User"
    message.from_user = mock_user
    
    # Mock bot
    bot = AsyncMock()
    message.bot = bot
    file_info = MagicMock()
    file_info.file_path = "path/to/voice.ogg"
    bot.get_file.return_value = file_info
    
    # Mock Whisper pipeline and load_audio
    with (
        patch("handlers.audio.pipe") as mock_pipe,
        patch("handlers.audio.load_audio") as mock_load_audio
    ):
        mock_load_audio.return_value = "mock_audio_data"
        mock_pipe.return_value = {"text": "Hello world"}
        
        # Mock directory creation and file writing
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.mkdir"),
            patch("builtins.open", MagicMock())
        ):
            
            await handle_audio_message(message)
            
            # Verify pipeline was called
            mock_pipe.assert_called_once_with("mock_audio_data")
            # Verify response was sent
            message.reply.assert_called_once_with("🎤 Transcription for Test User:\n\nHello world")

@pytest.mark.asyncio
async def test_handle_audio_file():
    # Mock message and bot
    message = AsyncMock(spec=Message)
    message.reply = AsyncMock()
    message.answer = AsyncMock()
    message.voice = None
    message.audio = MagicMock(spec=Audio)
    message.audio.file_id = "audio_file_id"
    message.audio.file_name = "test.mp3"
    
    # Mock from_user
    mock_user = MagicMock(spec=User)
    mock_user.id = 12345
    mock_user.full_name = "Test User"
    message.from_user = mock_user
    
    # Mock bot
    bot = AsyncMock()
    message.bot = bot
    file_info = MagicMock()
    file_info.file_path = "path/to/test.mp3"
    bot.get_file.return_value = file_info
    
    # Mock Whisper pipeline and load_audio
    with (
        patch("handlers.audio.pipe") as mock_pipe,
        patch("handlers.audio.load_audio") as mock_load_audio
    ):
        mock_load_audio.return_value = "mock_audio_data"
        mock_pipe.return_value = {"text": "Audio transcription test"}
        
        # Mock directory creation and file writing
        with (
            patch("pathlib.Path.mkdir"),
            patch("builtins.open", MagicMock())
        ):
            
            await handle_audio_message(message)
            
            # Verify pipeline was called
            mock_pipe.assert_called_once_with("mock_audio_data")
            # Verify response was sent
            message.reply.assert_called_once_with("🎤 Transcription for Test User:\n\nAudio transcription test")
