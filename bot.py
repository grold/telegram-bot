import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, AUDIO_CLEANUP_DAYS
from handlers import start, help, time, top, photo, group, auto_reply, weather, forecast, inline, log, audio, circle, camera, rate, mygroups
from tools.cleanup_audio import cleanup_old_audio
from database import init_db
from middlewares.command_logging import InteractionLoggingMiddleware
from middlewares.auth import AdminMiddleware
from middlewares.circle_location import CircleLocationMiddleware

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Initialize database
    init_db()

    # Run cleanup on startup if enabled
    if AUDIO_CLEANUP_DAYS > 0:
        logging.info(f"Running startup cleanup for old audio files (period: {AUDIO_CLEANUP_DAYS} days)...")
        cleanup_old_audio()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Register middlewares
    interaction_logger = InteractionLoggingMiddleware()
    dp.message.middleware(interaction_logger)
    dp.inline_query.middleware(interaction_logger)

    # Circle of Friends location tracking
    dp.message.middleware(CircleLocationMiddleware())

    admin_middleware = AdminMiddleware()
    log.router.message.middleware(admin_middleware)
    photo.router.message.middleware(admin_middleware)
    top.router.message.middleware(admin_middleware)
    mygroups.router.message.middleware(admin_middleware)

    # Register routers
    dp.include_router(inline.router) # Inline queries
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(time.router)
    dp.include_router(top.router)
    dp.include_router(photo.router)
    dp.include_router(forecast.router) # Forecast before weather
    dp.include_router(weather.router)
    from handlers import webcams
    dp.include_router(webcams.router)
    dp.include_router(group.router) # Moved before auto_reply.router
    dp.include_router(log.router) # Moved before auto_reply.router
    dp.include_router(audio.router)
    dp.include_router(circle.router)
    dp.include_router(camera.router)
    dp.include_router(rate.router)
    dp.include_router(mygroups.router)
    dp.include_router(auto_reply.router)

    # Start polling
    try:
        # Resolve used update types from all registered handlers
        allowed_updates = dp.resolve_used_update_types()
        
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
