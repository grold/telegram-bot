import pytest
from unittest.mock import AsyncMock, patch
from aiogram import types
from aiogram.filters import CommandObject
from handlers.rate import cmd_rate

# Mock data for default case (Base: RUB)
MOCK_RUB_RESPONSE = {
    "result": "success",
    "base_code": "RUB",
    "time_last_update_utc": "Fri, 04 Mar 2026 00:00:00 +0000",
    "rates": {
        "USD": 0.01,   # 1 RUB = 0.01 USD => 1 USD = 100 RUB
        "EUR": 0.009,  # 1 RUB = 0.009 EUR => 1 EUR = 111.11 RUB
        "JPY": 1.5,    # 1 RUB = 1.5 JPY => 1 JPY = 0.66 RUB
        "CNY": 0.07    # 1 RUB = 0.07 CNY => 1 CNY = 14.28 RUB
    }
}

# Mock data for custom case (Base: USD)
MOCK_USD_RESPONSE = {
    "result": "success",
    "base_code": "USD",
    "time_last_update_utc": "Fri, 04 Mar 2026 00:00:00 +0000",
    "rates": {
        "EUR": 0.90,
        "RUB": 100.0,
        "GBP": 0.75
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

@pytest.fixture
def message():
    msg = AsyncMock(spec=types.Message)
    msg.answer = AsyncMock()
    return msg

@pytest.mark.asyncio
async def test_cmd_rate_default(message):
    command = CommandObject(prefix="/", command="rate", args=None)
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(MOCK_RUB_RESPONSE, 200)
        
        await cmd_rate(message, command)
        
        # Verify call to API (should request RUB base)
        mock_get.assert_called_with("https://open.er-api.com/v6/latest/RUB", timeout=10)
        
        # Verify response content
        message.answer.assert_called()
        text = message.answer.call_args[0][0]
        
        assert "Exchange Rates (Base: RUB)" in text
        # Check inversions
        # 1 / 0.01 = 100.00
        assert "USD/RUB:</b> <code>100.00</code>" in text
        # 1 / 0.009 = 111.11
        assert "EUR/RUB:</b> <code>111.11</code>" in text
        # 1 / 1.5 = 0.67
        assert "JPY/RUB:</b> <code>0.67</code>" in text

@pytest.mark.asyncio
async def test_cmd_rate_custom_pair(message):
    command = CommandObject(prefix="/", command="rate", args="USD-EUR")
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(MOCK_USD_RESPONSE, 200)
        
        await cmd_rate(message, command)
        
        # Verify call to API (should request USD base)
        mock_get.assert_called_with("https://open.er-api.com/v6/latest/USD", timeout=10)
        
        # Verify response
        message.answer.assert_called()
        text = message.answer.call_args[0][0]
        
        assert "Exchange Rate (USD -> EUR)" in text
        assert "1 USD = <code>0.9000</code> EUR" in text

@pytest.mark.asyncio
async def test_cmd_rate_custom_pair_space(message):
    # Test space separator
    command = CommandObject(prefix="/", command="rate", args="USD EUR")
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse(MOCK_USD_RESPONSE, 200)
        
        await cmd_rate(message, command)
        
        mock_get.assert_called_with("https://open.er-api.com/v6/latest/USD", timeout=10)
        assert "Exchange Rate (USD -> EUR)" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_cmd_rate_invalid_args(message):
    command = CommandObject(prefix="/", command="rate", args="USD") # Missing second currency
    
    await cmd_rate(message, command)
    
    message.answer.assert_called_with("⚠️ Usage: <code>/rate USD-EUR</code> or <code>/rate USD EUR</code>")

@pytest.mark.asyncio
async def test_cmd_rate_api_error(message):
    command = CommandObject(prefix="/", command="rate", args=None)
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value = MockResponse({}, 500)
        
        await cmd_rate(message, command)
        
        assert "Service unavailable" in message.answer.call_args[0][0]
