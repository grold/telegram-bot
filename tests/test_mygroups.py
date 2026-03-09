import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from handlers.mygroups import cmd_mygroups

@pytest.mark.asyncio
async def test_cmd_mygroups_empty():
    with patch("handlers.mygroups.get_known_groups", return_value=[]):
        message = AsyncMock()
        await cmd_mygroups(message)
        message.answer.assert_called_once_with("No known groups found in logs.")

@pytest.mark.asyncio
async def test_cmd_mygroups_list():
    mock_groups = [
        {'chat_id': -100123, 'chat_title': 'Group A', 'chat_username': 'group_a_user', 'first_seen': '2026-01-01 10:00:00', 'last_seen': '2026-03-09 12:00:00'},
        {'chat_id': -100456, 'chat_title': 'Group B', 'chat_username': None, 'first_seen': '2026-02-01 11:00:00', 'last_seen': '2026-03-09 13:00:00'}
    ]
    with patch("handlers.mygroups.get_known_groups", return_value=mock_groups):
        message = AsyncMock()
        await cmd_mygroups(message)
        message.answer.assert_called_once()
        args = message.answer.call_args[0][0]
        assert "Group A" in args
        assert "Group B" in args
        assert "-100123" in args
        assert "-100456" in args
        assert "https://t.me/group_a_user" in args
        assert "https://t.me/c/456/1" in args
        assert "First seen: 2026-01-01 10:00:00" in args
        assert "First seen: 2026-02-01 11:00:00" in args
