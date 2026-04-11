import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, PhotoSize, User
from handlers.exif_weather import process_photo_for_exif
from handlers.camera import cmd_camera

@pytest.mark.asyncio
async def test_exif_weather_uses_chataction_sender():
    # Mock bot and message
    bot = AsyncMock()
    message = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 123
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1
    
    # Mock bot.get_file and bot.download_file
    file_mock = MagicMock()
    file_mock.file_path = "test/path"
    bot.get_file.return_value = file_mock
    
    # Mock file bytes
    file_bytes = io.BytesIO(b"fake_image_content")
    bot.download_file.return_value = file_bytes
    
    # Mock extract_exif_data and fetch_historical_weather
    with patch("handlers.exif_weather.extract_exif_data", return_value=((None, None), None)), \
         patch("aiogram.utils.chat_action.ChatActionSender.find_location", new_callable=MagicMock) as mock_sender_find_location:
        
        # We need to mock the context manager behavior
        mock_cm = AsyncMock()
        mock_sender_find_location.return_value = mock_cm
        
        await process_photo_for_exif(message, bot, "file_id_123")
        
        # Verify ChatActionSender.find_location was called
        mock_sender_find_location.assert_called_once()
        args, kwargs = mock_sender_find_location.call_args
        assert kwargs.get("bot") == bot
        assert kwargs.get("chat_id") == 123
        
        # Verify it was used as context manager
        mock_cm.__aenter__.assert_called_once()
        mock_cm.__aexit__.assert_called_once()

@pytest.mark.asyncio
async def test_camera_screenshot_uses_chataction_sender():
    # Mock message
    message = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 123
    message.bot = AsyncMock()
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    
    # Mock processing message
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "screenshot"
    
    # Mock get_camera_snapshot to return nothing to keep test simple
    with patch("handlers.camera.get_camera_snapshot", side_effect=Exception("Stop here")), \
         patch("aiogram.utils.chat_action.ChatActionSender.upload_photo", new_callable=MagicMock) as mock_sender_upload_photo:
        
        mock_cm = AsyncMock()
        mock_sender_upload_photo.return_value = mock_cm
        
        try:
            await cmd_camera(message, command)
        except Exception as e:
            if str(e) != "Stop here":
                raise
        
        # Verify ChatActionSender.upload_photo was called
        mock_sender_upload_photo.assert_called_once()
        args, kwargs = mock_sender_upload_photo.call_args
        assert kwargs.get("bot") == message.bot
        assert kwargs.get("chat_id") == 123
        
        # Verify it was used as context manager
        mock_cm.__aenter__.assert_called_once()
        mock_cm.__aexit__.assert_called_once()

@pytest.mark.asyncio
async def test_camera_video_uses_chataction_sender():
    # Mock message
    message = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 123
    message.bot = AsyncMock()
    message.answer = AsyncMock()
    
    # Mock processing message
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "video 5"
    
    # Mock get_camera_snapshot to return nothing to keep test simple
    with patch("handlers.camera.get_camera_snapshot", side_effect=Exception("Stop here")), \
         patch("aiogram.utils.chat_action.ChatActionSender.upload_video", new_callable=MagicMock) as mock_sender_upload_video:
        
        mock_cm = AsyncMock()
        mock_sender_upload_video.return_value = mock_cm
        
        try:
            await cmd_camera(message, command)
        except Exception as e:
            if str(e) != "Stop here":
                raise
        
        # Verify ChatActionSender.upload_video was called
        mock_sender_upload_video.assert_called_once()
        args, kwargs = mock_sender_upload_video.call_args
        assert kwargs.get("bot") == message.bot
        assert kwargs.get("chat_id") == 123
        
        # Verify it was used as context manager
        mock_cm.__aenter__.assert_called_once()
        mock_cm.__aexit__.assert_called_once()

import io
