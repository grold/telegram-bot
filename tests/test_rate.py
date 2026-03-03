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
        "Date": "2026-03-04T11:30:00+03:00",
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

    # Patch ClientSession.get. Note: we need to handle the connector argument in the constructor too if we mock it deeply, 
    # but mocking the get method directly is usually enough.
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(mock_data, 200)

        await cmd_rate(message)

        # Check if message.answer was called
        message.answer.assert_called_once()
        args, _ = message.answer.call_args
        response_text = args[0]
        
        assert "Exchange Rates (CBR.ru 04.03.2026)" in response_text
        assert "USD/RUB:</b> <code>100.50</code>" in response_text
        assert "EUR/RUB:</b> <code>110.20</code>" in response_text
        assert "JPY/RUB:</b> <code>0.65</code>" in response_text
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

        # The updated code returns status in the message
        args, _ = message.answer.call_args
        assert "returned an error (Status 500)" in args[0]
