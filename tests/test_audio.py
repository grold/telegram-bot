import pytest
import torch
import numpy as np
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
    
    # Mock from_user and chat
    mock_user = MagicMock(spec=User)
    mock_user.id = 12345
    mock_user.username = "testuser"
    mock_user.full_name = "Test User"
    message.from_user = mock_user
    
    mock_chat = MagicMock()
    mock_chat.title = "Test Group"
    mock_chat.id = 67890
    message.chat = mock_chat
    
    # Mock bot
    bot = AsyncMock()
    message.bot = bot
    file_info = MagicMock()
    file_info.file_path = "path/to/voice.ogg"
    bot.get_file.return_value = file_info
    
    # Mock Whisper components
    model = MagicMock()
    processor = MagicMock()
    pipe = MagicMock()
    
    # Mock return values for pipe
    pipe.return_value = {"text": "Hello world"}
    
    with (
        patch("handlers.audio.FFMPEG_AVAILABLE", True),
        patch("handlers.audio._get_whisper_components", return_value=(model, processor, pipe)),
        patch("handlers.audio.load_audio", return_value=np.zeros(16000)),
        patch("handlers.audio.ChatActionSender.typing", new_callable=MagicMock)
    ):
        # Mock directory creation and file writing
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.mkdir"),
            patch("builtins.open", MagicMock())
        ):
            
            await handle_audio_message(message)
            
            # Verify pipe was called
            assert pipe.called
            # Verify response was sent
            message.reply.assert_any_call("🎤 Transcription for Test User:\n\n<blockquote expandable>Hello world</blockquote>")

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
    
    # Mock from_user and chat
    mock_user = MagicMock(spec=User)
    mock_user.id = 12345
    mock_user.username = "testuser"
    mock_user.full_name = "Test User"
    message.from_user = mock_user
    
    mock_chat = MagicMock()
    mock_chat.title = "Test Group"
    mock_chat.id = 67890
    message.chat = mock_chat
    
    # Mock bot
    bot = AsyncMock()
    message.bot = bot
    file_info = MagicMock()
    file_info.file_path = "path/to/test.mp3"
    bot.get_file.return_value = file_info
    
    # Mock Whisper components
    model = MagicMock()
    processor = MagicMock()
    pipe = MagicMock()
    
    # Mock return values for pipe
    pipe.return_value = {"text": "Audio transcription test"}
    
    with (
        patch("handlers.audio.FFMPEG_AVAILABLE", True),
        patch("handlers.audio._get_whisper_components", return_value=(model, processor, pipe)),
        patch("handlers.audio.load_audio", return_value=np.zeros(16000)),
        patch("handlers.audio.ChatActionSender.typing", new_callable=MagicMock)
    ):
        # Mock directory creation and file writing
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.mkdir"),
            patch("builtins.open", MagicMock())
        ):
            
            await handle_audio_message(message)
            
            # Verify pipe was called
            assert pipe.called
            # Verify response was sent
            message.reply.assert_any_call("🎤 Transcription for Test User:\n\n<blockquote expandable>Audio transcription test</blockquote>")
