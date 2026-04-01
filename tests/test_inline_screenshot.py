import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.inline import inline_weather_handler
from aiogram.types import InlineQuery, User

@pytest.mark.asyncio
async def test_inline_screenshot_query_authorized():
    inline_query = MagicMock(spec=InlineQuery)
    inline_query.query = "screenshot"
    inline_query.from_user = MagicMock(spec=User)
    inline_query.from_user.id = 123
    inline_query.location = None
    inline_query.answer = AsyncMock()

    # Mock database and auth
    with patch("database.get_user") as mock_get_user, \
         patch("database.get_command_min_role") as mock_get_role:
        
        mock_get_role.return_value = "PUBLIC"
        mock_get_user.return_value = {"role": "USER", "is_authorized": 1}
        
        await inline_weather_handler(inline_query)
        
    inline_query.answer.assert_called_once()
    results = inline_query.answer.call_args[0][0]
    assert any(r.id == "camera_screenshot" for r in results)
