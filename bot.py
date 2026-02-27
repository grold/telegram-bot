import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import start, help, time, top, photo, group, auto_reply, weather, forecast, inline
from middlewares.command_logging import InteractionLoggingMiddleware

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

    # Register routers
    dp.include_router(inline.router) # Inline queries
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(time.router)
    dp.include_router(top.router)
    dp.include_router(photo.router)
    dp.include_router(forecast.router) # Forecast before weather
    dp.include_router(weather.router)
    dp.include_router(group.router)
    dp.include_router(auto_reply.router)

    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
