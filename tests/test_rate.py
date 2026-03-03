import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import types
from handlers.rate import cmd_rate

@pytest.mark.asyncio
async def test_cmd_rate_success():
    # Mock message
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()

    # Mock API responses for USD, EUR, JPY
    mock_responses = {
        "https://quote.rbc.ru/v2/publisher/ticker/item/USDRUB": {"data": {"last_price": 100.50}},
        "https://quote.rbc.ru/v2/publisher/ticker/item/EURRUB": {"data": {"last_price": 110.20}},
        "https://quote.rbc.ru/v2/publisher/ticker/item/JPYRUB": {"data": {"last_price": 0.65}}
    }

    class MockResponse:
        def __init__(self, url, status):
            self.url = url
            self.status = status
        async def json(self):
            return mock_responses.get(self.url, {})
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    with patch("aiohttp.ClientSession.get") as mock_get:
        def side_effect(url, **kwargs):
            return MockResponse(url, 200)
        mock_get.side_effect = side_effect

        await cmd_rate(message)

        # Check if message.answer was called
        message.answer.assert_called_once()
        args, _ = message.answer.call_args
        response_text = args[0]
        
        assert "USD/RUB:</b> <code>100.50</code>" in response_text
        assert "EUR/RUB:</b> <code>110.20</code>" in response_text
        assert "JPY/RUB:</b> <code>0.65</code>" in response_text
        assert "Valekoo reports" in response_text

@pytest.mark.asyncio
async def test_cmd_rate_partial_failure():
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()

    # Only USD and EUR succeed
    mock_responses = {
        "https://quote.rbc.ru/v2/publisher/ticker/item/USDRUB": {"data": {"last_price": 100.50}},
        "https://quote.rbc.ru/v2/publisher/ticker/item/EURRUB": {"data": {"last_price": 110.20}},
        "https://quote.rbc.ru/v2/publisher/ticker/item/JPYRUB": {} # Missing last_price
    }

    class MockResponse:
        def __init__(self, url, status):
            self.url = url
            self.status = status
        async def json(self):
            return mock_responses.get(self.url, {})
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    with patch("aiohttp.ClientSession.get") as mock_get:
        def side_effect(url, **kwargs):
            return MockResponse(url, 200)
        mock_get.side_effect = side_effect

        await cmd_rate(message)

        message.answer.assert_called_once()
        args, _ = message.answer.call_args
        response_text = args[0]
        
        assert "USD/RUB:</b> <code>100.50</code>" in response_text
        assert "JPY/RUB:</b> <i>Data unavailable</i>" in response_text
        assert "Valekoo reports" in response_text

@pytest.mark.asyncio
async def test_cmd_rate_total_failure():
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

        message.answer.assert_called_once_with("⚠️ Sorry, I couldn't fetch any exchange rates from RBC at the moment.")
