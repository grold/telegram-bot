import pytest
from unittest.mock import AsyncMock

from handlers.start import cmd_start

@pytest.mark.asyncio
async def test_start_command_handler():
    # Arrange
    message_mock = AsyncMock()

    # Act
    await cmd_start(message_mock)

    # Assert
    message_mock.answer.assert_called_once_with("Hello! I'm your Telegram bot. How can I help you today?")
