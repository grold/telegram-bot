import pytest
import sqlite3
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, User, Chat
from database import init_db, DATABASE_PATH, set_command_min_role, grant_user_access
from middlewares.auth import AuthMiddleware

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    # Clear DB
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM command_permissions")
    conn.commit()
    conn.close()

@pytest.mark.asyncio
async def test_auth_middleware_public_command():
    """Verify that any user can access a PUBLIC command."""
    middleware = AuthMiddleware()
    handler = AsyncMock()
    
    # Mock message
    user = User(id=111, is_bot=False, first_name="Test", username="tester")
    chat = Chat(id=111, type="private")
    message = Message(message_id=1, date=1, chat=chat, from_user=user, text="/weather")
    
    data = {}
    
    with patch.object(Message, 'answer', new_callable=AsyncMock) as mock_answer:
        await middleware(handler, message, data)
        handler.assert_awaited_once()
        assert data["user_role"] == "PUBLIC"
        assert data["is_authorized"] is False

@pytest.mark.asyncio
async def test_auth_middleware_admin_command_denied():
    """Verify that unauthorized user is blocked from ADMIN command."""
    middleware = AuthMiddleware()
    handler = AsyncMock()
    
    # Mock message for a legacy protected command
    user = User(id=222, is_bot=False, first_name="Test", username="tester")
    chat = Chat(id=222, type="private")
    message = Message(message_id=1, date=1, chat=chat, from_user=user, text="/log")
    
    data = {}
    
    with patch.object(Message, 'answer', new_callable=AsyncMock) as mock_answer:
        await middleware(handler, message, data)
        handler.assert_not_awaited()
        mock_answer.assert_awaited_once()
        assert "Access denied" in mock_answer.call_args[0][0]

@pytest.mark.asyncio
async def test_auth_middleware_admin_command_allowed_for_admin():
    """Verify that ADMIN user can access ADMIN command."""
    # Setup admin user
    grant_user_access(333, "ADMIN", username="admin_user")
    
    middleware = AuthMiddleware()
    handler = AsyncMock()
    
    user = User(id=333, is_bot=False, first_name="Admin", username="admin_user")
    chat = Chat(id=333, type="private")
    message = Message(message_id=1, date=1, chat=chat, from_user=user, text="/log")
    
    data = {}
    
    with patch.object(Message, 'answer', new_callable=AsyncMock) as mock_answer:
        await middleware(handler, message, data)
        handler.assert_awaited_once()
        assert data["user_role"] == "ADMIN"
        assert data["is_authorized"] is True

@pytest.mark.asyncio
async def test_auth_middleware_custom_access_level():
    """Verify that /set_access works via middleware logic."""
    # Set /weather to ADMIN level
    set_command_min_role("weather", "ADMIN")
    
    middleware = AuthMiddleware()
    handler = AsyncMock()
    
    user = User(id=444, is_bot=False, first_name="User", username="regular_user")
    chat = Chat(id=444, type="private")
    message = Message(message_id=1, date=1, chat=chat, from_user=user, text="/weather")
    
    data = {}
    
    with patch.object(Message, 'answer', new_callable=AsyncMock) as mock_answer:
        await middleware(handler, message, data)
        handler.assert_not_awaited()
        mock_answer.assert_awaited_once()
        assert "ADMIN" in mock_answer.call_args[0][0]
