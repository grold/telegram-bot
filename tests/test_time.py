import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.filters import CommandObject
from handlers.time import cmd_time

@pytest.mark.asyncio
async def test_time_command_handler_no_args():
    # Arrange
    message_mock = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = None

    # Act
    await cmd_time(message_mock, command_mock)

    # Assert
    message_mock.answer.assert_called_once()
    args, kwargs = message_mock.answer.call_args
    assert "Server Local Time" in args[0]
    assert kwargs.get("parse_mode") == "HTML"

@pytest.mark.asyncio
async def test_time_command_handler_with_city():
    # Arrange
    message_mock = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = "London"

    with patch('handlers.time.geolocator.geocode') as mock_geocode, \
         patch('handlers.time.tf') as mock_tf:
        
        # Setup mocks
        mock_location = MagicMock()
        mock_location.address = "London, UK"
        mock_location.longitude = -0.1276
        mock_location.latitude = 51.5072
        mock_geocode.return_value = mock_location
        
        mock_tf.timezone_at.return_value = "Europe/London"

        # Act
        await cmd_time(message_mock, command_mock)

        # Assert
        message_mock.answer.assert_called_once()
        args, kwargs = message_mock.answer.call_args
        text = args[0]
        assert "London" in text
        assert "Europe/London" in text
        assert kwargs.get("parse_mode") == "HTML"

@pytest.mark.asyncio
async def test_time_command_handler_city_not_found():
    # Arrange
    message_mock = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = "InvalidCityxyz"

    with patch('handlers.time.geolocator.geocode') as mock_geocode:
        mock_geocode.return_value = None

        # Act
        await cmd_time(message_mock, command_mock)

        # Assert
        message_mock.answer.assert_called_once_with("Sorry, I couldn't find the location: 'InvalidCityxyz'.")
