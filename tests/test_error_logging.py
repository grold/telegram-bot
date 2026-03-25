import pytest
import sqlite3
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Chat
from middlewares.command_logging import InteractionLoggingMiddleware
from database import init_db, get_recent_logs, add_interaction_log
from config import DATABASE_PATH

@pytest.fixture(autouse=True)
def setup_database():
    """Ensure the database is initialized before each test."""
    init_db()
    # Clear logs table for a clean test state
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs")
    conn.commit()
    conn.close()

@pytest.mark.asyncio
async def test_middleware_logs_exception():
    # 1. Setup mock middleware and failing handler
    middleware = InteractionLoggingMiddleware()
    error_message = "Test exception for logging"
    handler = AsyncMock(side_effect=ValueError(error_message))
    
    # Mock Aiogram event
    user_id = 12345
    event = MagicMock(spec=Message)
    event.from_user = MagicMock(spec=User, id=user_id, username="testuser", full_name="Test User", language_code="en")
    event.chat = MagicMock(spec=Chat, id=67890, type="private", title=None, username=None)
    event.message_id = 111
    event.text = "/cause_error"
    
    data = {"user_role": "ADMIN"}
    
    # 2. Call middleware (it should re-raise the exception)
    with pytest.raises(ValueError, match=error_message):
        await middleware(handler, event, data)
    
    # Give some time for the background task to complete
    await asyncio.sleep(0.1)
    
    # 3. Assert the log entry in the database
    logs = get_recent_logs(limit=1)
    assert len(logs) == 1
    log = logs[0]
    
    assert log['user_id'] == user_id
    assert log['content'] == "/cause_error"
    assert log['status'] == 'ERROR'
    assert log['exception'] == 'ValueError'
    assert error_message in log['traceback']
    assert 'traceback' in log['traceback'].lower()
    assert log['user_role'] == 'ADMIN'

@pytest.mark.asyncio
async def test_middleware_logs_success():
    # Verify it still logs successful commands correctly
    middleware = InteractionLoggingMiddleware()
    handler = AsyncMock(return_value="OK")
    
    event = MagicMock(spec=Message)
    event.from_user = MagicMock(spec=User, id=999, username="success_user", full_name="Success User", language_code="en")
    event.chat = MagicMock(spec=Chat, id=888, type="private")
    event.message_id = 222
    event.text = "/success"
    
    data = {"user_role": "USER"}
    
    result = await middleware(handler, event, data)
    assert result == "OK"
    
    # Give some time for the background task to complete
    await asyncio.sleep(0.1)
    
    logs = get_recent_logs(limit=1)
    assert len(logs) == 1
    log = logs[0]
    
    assert log['user_id'] == 999
    assert log['status'] == 'SUCCESS'
    assert log['exception'] is None
    assert log['traceback'] is None
