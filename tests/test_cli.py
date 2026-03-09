import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from cli import execute_command
from tools.mock_aiogram import MockMessage, MockCommandObject

@pytest.mark.asyncio
async def test_cli_help():
    with patch("handlers.help.cmd_help", new_callable=AsyncMock) as mock_help:
        args = MagicMock()
        args.command = "help"
        await execute_command(args)
        mock_help.assert_called_once()

@pytest.mark.asyncio
async def test_cli_start():
    with patch("handlers.start.cmd_start", new_callable=AsyncMock) as mock_start:
        args = MagicMock()
        args.command = "start"
        await execute_command(args)
        mock_start.assert_called_once()

@pytest.mark.asyncio
async def test_cli_weather():
    with patch("handlers.weather.cmd_weather", new_callable=AsyncMock) as mock_weather:
        args = MagicMock()
        args.command = "weather"
        args.city = "London"
        await execute_command(args)
        mock_weather.assert_called_once()
        # Check if command object has the right args
        call_args = mock_weather.call_args[0]
        assert call_args[1].args == "London"

@pytest.mark.asyncio
async def test_cli_rate():
    with patch("handlers.rate.cmd_rate", new_callable=AsyncMock) as mock_rate:
        args = MagicMock()
        args.command = "rate"
        args.pair = "USD-EUR"
        await execute_command(args)
        mock_rate.assert_called_once()
        call_args = mock_rate.call_args[0]
        assert call_args[1].args == "USD-EUR"

@pytest.mark.asyncio
async def test_cli_log():
    with patch("handlers.log.cmd_log", new_callable=AsyncMock) as mock_log:
        args = MagicMock()
        args.command = "log"
        args.num = "5"
        args.query = ["test"]
        await execute_command(args)
        mock_log.assert_called_once()
        call_args = mock_log.call_args[0]
        assert "5 test" in call_args[1].args
