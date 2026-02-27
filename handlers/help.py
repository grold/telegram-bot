from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "<b>Inline Mode</b>\n"
        "You can use this bot in any chat by typing its username "
        "and a city name (e.g., <code>@YourBotName London</code>) to quickly get the weather.\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/time [city] - Show current time in specified city (default: Server local time)\n"
        "/weather [city] - Show current weather for a city or your location\n"
        "/forecast [city] - Show 5-day weather forecast for a city or your location\n"
        "/top - Show system resource usage\n"
        "/photo - Send a random photo"
    )
    await message.answer(help_text, parse_mode="HTML")
