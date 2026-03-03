import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User
from handlers.camera import cmd_camera

@pytest.mark.asyncio
async def test_cmd_camera_screenshot_success():
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
    
    # Mock ONVIF
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_snapshot:
        mock_get_snapshot.return_value = "http://10.1.100.151/snapshot.jpg"
        
        # Mock httpx
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = mock_client_class.return_value.__aenter__.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"fake_image_content"
            mock_client.get = AsyncMock(return_value=mock_response)
            
            await cmd_camera(message, command)
            
            # Verify snapshot was requested
            mock_get_snapshot.assert_called_once()
            # Verify image was downloaded
            mock_client.get.assert_called()
            # Verify photo was sent
            message.answer_photo.assert_called_once()
            # Verify processing message was deleted
            processing_msg.delete.assert_called_once()

@pytest.mark.asyncio
async def test_cmd_camera_invalid_args():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    command = MagicMock()
    command.args = "invalid"
    
    await cmd_camera(message, command)
    
    message.answer.assert_called_with("Usage: <code>/camera screenshot</code>")

@pytest.mark.asyncio
async def test_cmd_camera_screenshot_onvif_failure():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    command = MagicMock()
    command.args = "screenshot"
    
    with patch("handlers.camera.get_camera_snapshot", new_callable=AsyncMock) as mock_get_snapshot:
        mock_get_snapshot.side_effect = Exception("ONVIF Error")
        
        await cmd_camera(message, command)
        
        # Verify error message sent
        message.answer.assert_any_call("❌ Error capturing screenshot: ONVIF Error")
