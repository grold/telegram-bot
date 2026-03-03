import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import types
from handlers.rate import cmd_rate

@pytest.mark.asyncio
async def test_cmd_rate_success():
    # Mock message
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()

    # Mock CBR API response
    mock_data = {
        "Valute": {
            "USD": {"Value": 100.50},
            "EUR": {"Value": 110.20},
            "JPY": {"Value": 65.00, "Nominal": 100}
        }
    }

    class MockResponse:
        def __init__(self, data, status):
            self._data = data
            self.status = status
        async def json(self):
            return self._data
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(mock_data, 200)

        await cmd_rate(message)

        # Check if message.answer was called
        message.answer.assert_called_once()
        args, _ = message.answer.call_args
        response_text = args[0]
        
        assert "USD/RUB:</b> <code>100.50</code>" in response_text
        assert "EUR/RUB:</b> <code>110.20</code>" in response_text
        assert "JPY/RUB:</b> <code>0.65</code>" in response_text # 65.00 / 100
        assert "Valekoo reports" in response_text

@pytest.mark.asyncio
async def test_cmd_rate_failure():
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()

    class MockResponse:
        def __init__(self, status):
            self.status = status
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(500)

        await cmd_rate(message)

        message.answer.assert_called_once_with("⚠️ Sorry, the exchange rate service is currently unavailable.")
