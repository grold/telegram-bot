import pytest
import requests
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User
from handlers.camera import cmd_camera

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
            
            await cmd_camera(message, command)
            
            # Verify snapshot was requested
            mock_get_uris.assert_called_once()
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
                
                await cmd_camera(message, command)
                
                # Verify RTSP fallback was called
                mock_capture_rtsp.assert_called_once()
                # Verify photo was sent
                message.answer_photo.assert_called_once()

@pytest.mark.asyncio
async def test_cmd_camera_invalid_args():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    command = MagicMock()
    command.args = "invalid"
    
    await cmd_camera(message, command)
    
    message.answer.assert_called_with("Usage: <code>/camera screenshot</code>")

@pytest.mark.asyncio
async def test_cmd_camera_screenshot_all_fail():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    command = MagicMock()
    command.args = "screenshot"
    
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_uris:
        mock_get_uris.return_value = (None, None)
        
        await cmd_camera(message, command)
        
        message.answer.assert_any_call("❌ Failed to capture image from both Snapshot URI and RTSP stream. The camera might be busy or credentials might be incorrect for the stream.")
