import pytest
import requests
from unittest.mock import AsyncMock, MagicMock, patch, mock_open, ANY
from aiogram.types import Message, User
from handlers.camera import cmd_camera
from pathlib import Path

@pytest.mark.asyncio
async def test_cmd_camera_screenshot_uri_success():
    # Mock message
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1
    
    # Mock processing message
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "screenshot"
    
    # Mock URIs
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_snapshot_uri = "http://10.1.100.151/snapshot.jpg"
        mock_get_uris.return_value = (mock_get_snapshot_uri, "rtsp://10.1.100.151/stream")
        
        # Mock requests.get for Snapshot URI
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"fake_image_content"
            mock_get.return_value = mock_response
            
            # Mock filesystem operations
            with patch("pathlib.Path.mkdir"), \
                 patch("builtins.open", mock_open()) as mocked_file:
                
                await cmd_camera(message, command)
                
                # Verify snapshot was requested
                mock_get_uris.assert_called_once()
                # Verify file was saved
                mocked_file.assert_called()
                mocked_file().write.assert_called_with(b"fake_image_content")
                # Verify photo was sent
                message.answer_photo.assert_called_once()

@pytest.mark.asyncio
async def test_cmd_camera_screenshot_rtsp_fallback_success():
    # Mock message
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1
    
    # Mock processing message
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "screenshot"
    
    # Mock URIs (Snapshot fails, RTSP available)
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_uris.return_value = ("http://10.1.100.151/fail.jpg", "rtsp://10.1.100.151/stream")
        
        # Mock Snapshot failure
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404
            mock_get.return_value.content = b""
            
            # Mock RTSP capture success
            with patch("handlers.camera.capture_rtsp_frame", new_callable=AsyncMock) as mock_capture_rtsp:
                mock_capture_rtsp.return_value = b"rtsp_frame_content"
                
                # Mock filesystem operations
                with patch("pathlib.Path.mkdir"), \
                     patch("builtins.open", mock_open()) as mocked_file:
                    
                    await cmd_camera(message, command)
                    
                    # Verify RTSP fallback was called
                    mock_capture_rtsp.assert_called_once()
                    # Verify file was saved
                    mocked_file().write.assert_called_with(b"rtsp_frame_content")
                    # Verify photo was sent
                    message.answer_photo.assert_called_once()

@pytest.mark.asyncio
async def test_cmd_camera_video_success():
    # Mock message
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_video = AsyncMock()
    
    # Mock processing message
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "video 10"
    
    # Mock URIs
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_uris.return_value = (None, "rtsp://10.1.100.151/stream")
        
        # Mock record_rtsp_video success
        with patch("handlers.camera.record_rtsp_video", new_callable=AsyncMock) as mock_record:
            mock_record.return_value = True
            
            # Mock filesystem operations
            with patch("pathlib.Path.mkdir"), \
                 patch("pathlib.Path.exists", return_value=True), \
                 patch("pathlib.Path.stat") as mock_stat:
                
                mock_stat.return_value.st_size = 1000
                
                await cmd_camera(message, command)
                
                # Verify video was recorded with correct duration
                mock_record.assert_called_with("rtsp://10.1.100.151/stream", 10, ANY)
                # Verify video was sent
                message.answer_video.assert_called_once()
                # Verify processing message was deleted
                processing_msg.delete.assert_called_once()

@pytest.mark.asyncio
async def test_cmd_camera_video_default_duration():
    # Mock message
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_video = AsyncMock()
    
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "video"
    
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_uris.return_value = (None, "rtsp://10.1.100.151/stream")
        
        with patch("handlers.camera.record_rtsp_video", new_callable=AsyncMock) as mock_record:
            mock_record.return_value = True
            with patch("pathlib.Path.mkdir"), \
                 patch("pathlib.Path.exists", return_value=True), \
                 patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000
                
                await cmd_camera(message, command)
                
                # Verify default duration of 5s
                mock_record.assert_called_with("rtsp://10.1.100.151/stream", 5, ANY)

@pytest.mark.asyncio
async def test_cmd_camera_video_max_duration():
    # Mock message
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_video = AsyncMock()
    
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "video 999"  # Exceeds MAX_VIDEO_DURATION (30)
    
    from config import MAX_VIDEO_DURATION

    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_uris.return_value = (None, "rtsp://10.1.100.151/stream")
        
        with patch("handlers.camera.record_rtsp_video", new_callable=AsyncMock) as mock_record:
            mock_record.return_value = True
            with patch("pathlib.Path.mkdir"), \
                 patch("pathlib.Path.exists", return_value=True), \
                 patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000
                
                await cmd_camera(message, command)
                
                # Verify duration was capped at MAX_VIDEO_DURATION
                mock_record.assert_called_with("rtsp://10.1.100.151/stream", MAX_VIDEO_DURATION, ANY)

@pytest.mark.asyncio
async def test_cmd_camera_video_invalid_args():
    # Mock message
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.answer_video = AsyncMock()
    
    processing_msg = AsyncMock()
    message.answer.return_value = processing_msg
    
    command = MagicMock()
    command.args = "video abc"
    
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_uris.return_value = (None, "rtsp://10.1.100.151/stream")
        
        with patch("handlers.camera.record_rtsp_video", new_callable=AsyncMock) as mock_record:
            mock_record.return_value = True
            with patch("pathlib.Path.mkdir"), \
                 patch("pathlib.Path.exists", return_value=True), \
                 patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000
                
                await cmd_camera(message, command)
                
                # Verify fallback to default duration of 5s
                mock_record.assert_called_with("rtsp://10.1.100.151/stream", 5, ANY)

@pytest.mark.asyncio
async def test_cmd_camera_help():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    command = MagicMock()
    command.args = ""
    
    await cmd_camera(message, command)
    
    message.answer.assert_called_with("Usage:\n<code>/camera screenshot</code>\n<code>/camera video [sec]</code>")

@pytest.mark.asyncio
async def test_cmd_camera_screenshot_all_fail():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    command = MagicMock()
    command.args = "screenshot"
    
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_uris.return_value = (None, None)
        
        await cmd_camera(message, command)
        
        message.answer.assert_any_call("❌ Failed to capture image from both Snapshot URI and RTSP stream.")
