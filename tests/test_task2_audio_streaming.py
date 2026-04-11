import pytest
import numpy as np
import torch
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Voice
from handlers.audio import handle_audio_message, TelegramStreamer

@pytest.mark.asyncio
async def test_telegram_streamer_updates_message():
    loop = asyncio.get_event_loop()
    message = AsyncMock()
    processor = MagicMock()
    processor.batch_decode.return_value = ["Hello world"]
    
    streamer = TelegramStreamer(message, processor, interval=0)
    
    import handlers.audio
    with patch.object(handlers.audio.asyncio, "run_coroutine_threadsafe") as mock_run:
        # Simulate putting a token
        token = torch.tensor([[1]])
        streamer.put(token)
        
        print(f"DEBUG: tokens={streamer.tokens}")
        print(f"DEBUG: text='{streamer.text}'")
        print(f"DEBUG: mock_run.called={mock_run.called}")
        assert mock_run.called

@pytest.mark.asyncio
async def test_handle_audio_message_uses_chataction_sender():
    import handlers.audio
    handlers.audio._whisper_model = None
    handlers.audio._whisper_processor = None
    handlers.audio._whisper_pipe = None
    
    message = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 123
    message.voice = MagicMock(spec=Voice)
    message.voice.file_id = "voice_id"
    message.from_user = MagicMock(spec=User)
    message.from_user.full_name = "Test User"
    message.from_user.username = "testuser"
    
    bot = AsyncMock()
    message.bot = bot
    
    # Mock Whisper components
    model = MagicMock()
    generate_mock = MagicMock(return_value=torch.tensor([[1, 2, 3]]))
    model.generate = generate_mock
    processor = MagicMock()
    pipe = MagicMock()
    
    # Mock return values
    processor.batch_decode.return_value = ["Transcribed text"]
    processor.return_value.input_features = torch.tensor([[[1.0]]])
    
    async def mock_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    with patch("handlers.audio.FFMPEG_AVAILABLE", True), \
         patch("handlers.audio._get_whisper_components", return_value=(model, processor, pipe)), \
         patch("handlers.audio.load_audio", return_value=np.zeros(16000)), \
         patch("handlers.audio.asyncio.to_thread", side_effect=mock_to_thread), \
         patch("handlers.audio.ChatActionSender.typing", new_callable=MagicMock) as mock_typing:
        
        mock_cm = AsyncMock()
        mock_typing.return_value = mock_cm
        
        # Mock bot methods
        bot.get_file.return_value = MagicMock(file_path="path/to/file")
        bot.download_file = AsyncMock()
        
        # Mock message.reply to return a status_msg
        status_msg = AsyncMock()
        message.reply.return_value = status_msg
        
        # Mock directory creation and file writing
        with patch("pathlib.Path.mkdir"), \
             patch("builtins.open", MagicMock()):
            await handle_audio_message(message)
        
        # Verify ChatActionSender.typing was called
        mock_typing.assert_called_once()
        # Verify model.generate was called
        assert generate_mock.called


