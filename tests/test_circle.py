import pytest
import os
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Location
from handlers.circle import cmd_share, cmd_map, handle_circle_location_update
from database import init_db, get_user, update_user_status, update_user_location

@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = tmp_path / "test_map.db"
    # Ensure database.DATABASE_PATH is patched everywhere it's used
    with patch("database.DATABASE_PATH", str(db_path)):
        init_db()
        yield db_path

@pytest.mark.asyncio
async def test_cmd_share_on():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1
    message.from_user.username = "user1"
    message.from_user.full_name = "User One"
    
    command = MagicMock()
    command.args = "on"
    
    await cmd_share(message, command)
    
    # Verify DB update
    user = get_user(1)
    assert user['is_sharing'] == 1
    # Verify response
    message.answer.assert_called()

@pytest.mark.asyncio
async def test_cmd_map_mutual_privacy():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1
    
    # User 1 is NOT sharing
    update_user_status(1, "user1", "User One", False)
    
    command = MagicMock()
    command.args = "list"
    
    await cmd_map(message, command)
    
    # Verify denied access
    message.answer.assert_called_with("You must turn on location sharing (<code>/share on</code>) to see other users.")

@pytest.mark.asyncio
async def test_location_auto_update():
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1
    message.from_user.username = "user1"
    message.location = MagicMock(spec=Location)
    message.location.latitude = 50.0
    message.location.longitude = 30.0
    
    # User 1 is sharing
    update_user_status(1, "user1", "User One", True)
    
    await handle_circle_location_update(message)
    
    # Verify location stored
    user = get_user(1)
    assert user['latitude'] == 50.0
    assert user['longitude'] == 30.0

@pytest.mark.asyncio
async def test_cmd_map_list_success():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 1
    
    # User 1 (requester) is sharing
    update_user_status(1, "user1", "User One", True)
    update_user_location(1, 10.0, 10.0)
    
    # User 2 is also sharing
    update_user_status(2, "user2", "User Two", True)
    update_user_location(2, 20.0, 20.0)
    
    command = MagicMock()
    command.args = "list"
    
    await cmd_map(message, command)
    
    # Verify User 2 is in the list
    args, kwargs = message.answer.call_args
    assert "user2" in args[0]
