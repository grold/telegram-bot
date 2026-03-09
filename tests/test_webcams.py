import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.filters import CommandObject
from handlers.webcams import cmd_webcams, get_webcams_list, get_webcam_details
from aiogram import types

@pytest.fixture
def message_mock():
    mock = AsyncMock(spec=types.Message)
    mock.answer = AsyncMock()
    mock.answer_photo = AsyncMock()
    mock.edit_text = AsyncMock()
    return mock

@pytest.fixture
def command_mock():
    return MagicMock(spec=CommandObject)

@pytest.mark.asyncio
async def test_cmd_webcams_help(message_mock, command_mock):
    command_mock.args = None
    await cmd_webcams(message_mock, command_mock)
    message_mock.answer.assert_called_once()
    assert "Windy Webcams Commands" in message_mock.answer.call_args[0][0]

@pytest.mark.asyncio
@patch("handlers.webcams.get_weather")
@patch("handlers.webcams.get_webcams_list")
async def test_cmd_webcams_city(mock_get_list, mock_get_weather, message_mock, command_mock):
    command_mock.args = "city London"
    
    # Mock weather response
    mock_get_weather.return_value = {
        "coord": {"lat": 51.5074, "lon": -0.1278},
        "name": "London",
        "sys": {"country": "GB"}
    }
    
    # Mock webcam response
    mock_get_list.return_value = {
        "webcams": [
            {
                "webcamId": "12345",
                "title": "London Eye",
                "location": {"city": "London", "country": "GB"},
                "images": {
                    "current": {
                        "preview": "http://example.com/image.jpg"
                    }
                }
            }
        ]
    }
    
    # Call the handler
    # Note: message.answer is called first with "Searching...", then edit_text, or deleted and answer_photo
    # In implementation: msg = answer("Searching") -> get_weather -> get_list -> answer_photo -> msg.delete
    
    # We need to mock the return value of message.answer so we can track calls on it
    msg_mock = AsyncMock()
    message_mock.answer.return_value = msg_mock
    
    await cmd_webcams(message_mock, command_mock)
    
    # Check flow
    mock_get_weather.assert_called_with(city_name="London")
    mock_get_list.assert_called()
    assert "nearby" in mock_get_list.call_args[1]
    
    # Should send photo
    message_mock.answer_photo.assert_called_once()
    args, kwargs = message_mock.answer_photo.call_args
    assert args[0] == "http://example.com/image.jpg"
    assert "London Eye" in kwargs["caption"]

@pytest.mark.asyncio
@patch("handlers.webcams.get_webcams_list")
async def test_cmd_webcams_list(mock_get_list, message_mock, command_mock):
    command_mock.args = "list"
    
    mock_get_list.return_value = {
        "webcams": [
            {
                "webcamId": "101",
                "title": "Beach Cam",
                "location": {"city": "Miami", "country": "US"}
            }
        ]
    }
    
    await cmd_webcams(message_mock, command_mock)
    
    mock_get_list.assert_called_with(limit=5)
    message_mock.answer.assert_called()
    assert "Beach Cam" in message_mock.answer.call_args[0][0]

@pytest.mark.asyncio
@patch("handlers.webcams.get_weather")
@patch("handlers.webcams.get_webcams_list")
async def test_cmd_webcams_cities(mock_get_list, mock_get_weather, message_mock, command_mock):
    command_mock.args = "cities London"
    
    mock_get_weather.return_value = {
        "coord": {"lat": 51.5074, "lon": -0.1278},
        "name": "London"
    }
    
    mock_get_list.return_value = {
        "webcams": [
            {"webcamId": "1", "title": "Cam 1"},
            {"webcamId": "2", "title": "Cam 2"}
        ]
    }
    
    msg_mock = AsyncMock()
    message_mock.answer.return_value = msg_mock
    
    await cmd_webcams(message_mock, command_mock)
    
    msg_mock.edit_text.assert_called()
    assert "Cam 1" in msg_mock.edit_text.call_args[0][0]
    assert "Cam 2" in msg_mock.edit_text.call_args[0][0]

@pytest.mark.asyncio
@patch("handlers.webcams.get_webcam_details")
async def test_cmd_webcams_id_fix(mock_get_details, message_mock, command_mock):
    command_mock.args = "id 12345"
    
    # Test with string player URLs (the fix) and images
    mock_get_details.return_value = {
        "webcamId": "12345",
        "title": "Test Cam",
        "status": "active",
        "location": {"city": "Test City", "country": "TC"},
        "images": {"current": {"preview": "http://example.com/p.jpg"}},
        "player": {"day": "http://player.url/day", "live": "http://player.url/live"}
    }
    
    await cmd_webcams(message_mock, command_mock)
    
    message_mock.answer_photo.assert_called()
    assert "Watch Live/Timelapse" in message_mock.answer_photo.call_args[1]["caption"]
    assert "http://player.url/live" in message_mock.answer_photo.call_args[1]["caption"]


