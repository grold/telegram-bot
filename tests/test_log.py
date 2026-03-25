import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from handlers.log import cmd_log
from aiogram.filters import CommandObject

@pytest.mark.asyncio
async def test_log_command_no_args():
    message_mock = AsyncMock()
    command_mock = CommandObject(prefix='/', command='log', args=None)
    
    # Mocking logs with status and exception fields
    mock_logs = [
        {'timestamp': '2024-03-03 13:28:11', 'username': 'user1', 'full_name': 'User One', 
         'chat_title': 'Group A', 'content': '/start', 'duration_ms': 100.0, 'bot_version': '0.4.0',
         'status': 'SUCCESS', 'exception': None, 'user_role': 'ADMIN'}
    ]
    
    with patch('handlers.log.get_recent_logs', return_value=mock_logs):
        await cmd_log(message_mock, command_mock, user_role='ADMIN')
        
    message_mock.answer.assert_called_once()
    args, _ = message_mock.answer.call_args
    assert "user1" in args[0]
    assert "Group A" in args[0]
    assert "0.4.0" in args[0]
    assert "✅ 2024-03-03 13:28:11" in args[0]

@pytest.mark.asyncio
async def test_log_command_with_errors_filter():
    message_mock = AsyncMock()
    command_mock = CommandObject(prefix='/', command='log', args='errors')
    
    with patch('handlers.log.get_recent_logs', return_value=[]) as mock_get:
        await cmd_log(message_mock, command_mock, user_role='ADMIN')
        mock_get.assert_called_once_with(10, None, 'ERROR')

@pytest.mark.asyncio
async def test_log_command_with_limit_and_errors():
    message_mock = AsyncMock()
    command_mock = CommandObject(prefix='/', command='log', args='50 errors')
    
    with patch('handlers.log.get_recent_logs', return_value=[]) as mock_get:
        await cmd_log(message_mock, command_mock, user_role='ADMIN')
        mock_get.assert_called_once_with(50, None, 'ERROR')

@pytest.mark.asyncio
async def test_log_command_with_limit():
    message_mock = AsyncMock()
    command_mock = CommandObject(prefix='/', command='log', args='5')
    
    with patch('handlers.log.get_recent_logs', return_value=[]) as mock_get:
        await cmd_log(message_mock, command_mock, user_role='ADMIN')
        mock_get.assert_called_once_with(5, None, None)

@pytest.mark.asyncio
async def test_log_command_with_query():
    message_mock = AsyncMock()
    command_mock = CommandObject(prefix='/', command='log', args='@user1')
    
    with patch('handlers.log.get_recent_logs', return_value=[]) as mock_get:
        await cmd_log(message_mock, command_mock, user_role='ADMIN')
        mock_get.assert_called_once_with(10, '@user1', None)

@pytest.mark.asyncio
async def test_log_command_with_limit_and_query():
    message_mock = AsyncMock()
    command_mock = CommandObject(prefix='/', command='log', args='20 group_name')
    
    with patch('handlers.log.get_recent_logs', return_value=[]) as mock_get:
        await cmd_log(message_mock, command_mock, user_role='ADMIN')
        mock_get.assert_called_once_with(20, 'group_name', None)

@pytest.mark.asyncio
async def test_log_command_empty():
    message_mock = AsyncMock()
    command_mock = CommandObject(prefix='/', command='log', args='nonexistent')
    
    with patch('handlers.log.get_recent_logs', return_value=[]):
        await cmd_log(message_mock, command_mock, user_role='ADMIN')
        
    message_mock.answer.assert_called_once_with("Log database is empty for query: 'nonexistent'")
