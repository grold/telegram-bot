from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import bot

@pytest.mark.asyncio
async def test_bot_main_logging():
    # Mocking dependencies
    with patch("bot.init_db") as mock_init_db, \
         patch("bot.migrate_auth_file") as mock_migrate, \
         patch("bot.Bot") as mock_bot, \
         patch("bot.Dispatcher") as mock_dp, \
         patch("bot.cleanup_old_audio") as mock_cleanup, \
         patch("logging.info") as mock_logging_info, \
         patch("bot.InteractionLoggingMiddleware") as mock_interaction_middleware, \
         patch("bot.AuthMiddleware") as mock_auth_middleware, \
         patch("bot.CircleLocationMiddleware") as mock_circle_middleware:
        
        # Mocking objects that are initialized
        mock_bot_instance = MagicMock()
        mock_bot_instance.session = MagicMock()
        mock_bot_instance.session.close = AsyncMock()
        mock_bot.return_value = mock_bot_instance
        
        mock_dp_instance = MagicMock()
        mock_dp.return_value = mock_dp_instance
        
        # We need to mock awaitable start_polling() to avoid hanging the test
        mock_dp_instance.start_polling = AsyncMock()

        # Let's run a bit of main(), we can't run it fully easily as it's a long running task
        # But we can patch asyncio.run or just call main() and catch the first failure after logging
        
        # Let's just mock the version import and call the logger directly to see if it's available in bot namespace
        assert hasattr(bot, "BOT_VERSION")
        
        # Now let's try calling main and stop early
        with patch("asyncio.gather", side_effect=Exception("stop_execution")):
            try:
                await bot.main()
            except Exception as e:
                if str(e) != "stop_execution":
                    raise

        # Check if version was logged
        # The logging call is: logging.info(f"Telegram Bot version {BOT_VERSION} started.")
        any_bot_version_log = any(
            "Telegram Bot version" in call[0][0] and "started" in call[0][0]
            for call in mock_logging_info.call_args_list
        )
        assert any_bot_version_log
