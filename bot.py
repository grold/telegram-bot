import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, help, time, top, photo, group, auto_reply, weather, forecast, inline, log, poll
from middlewares.command_logging import InteractionLoggingMiddleware
from middlewares.auth import AdminMiddleware

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register middlewares
    interaction_logger = InteractionLoggingMiddleware()
    dp.message.middleware(interaction_logger)
    dp.inline_query.middleware(interaction_logger)

    admin_middleware = AdminMiddleware()
    log.router.message.middleware(admin_middleware)
    photo.router.message.middleware(admin_middleware)
    top.router.message.middleware(admin_middleware)
    poll.router.message.middleware(admin_middleware)

    # Register routers
    dp.include_router(poll.router) # Poll handler
    dp.include_router(inline.router) # Inline queries
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(time.router)
    dp.include_router(top.router)
    dp.include_router(photo.router)
    dp.include_router(forecast.router) # Forecast before weather
    dp.include_router(weather.router)
    dp.include_router(group.router) # Moved before auto_reply.router
    dp.include_router(log.router) # Moved before auto_reply.router
    dp.include_router(auto_reply.router)

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
