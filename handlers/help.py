from aiogram import Router, types
from aiogram.filters import Command
from config import BOT_VERSION, TOP_NUM_LINES, LOG_NUM_LINES

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        f"<b>🤖 Bot Version:</b> <code>{BOT_VERSION}</code>\n\n"
        "<b>✨ Inline Mode</b>\n"
        "Type <code>@groldtestbot [city]</code> in any chat for quick weather. "
        "Try <code>@groldtestbot</code> without text to use your current location!\n\n"
        "<b>🛠️ Available Commands:</b>\n"
        "/start - Welcome message\n"
        "/help - Show this guide\n"
        "/time [city] - Local time (default: Server time)\n"
        "/weather [city] - Current weather or live location\n"
        "/forecast [city] - 5-day weather forecast\n"
        "/photo - Send a random photo\n"
        "/top - Server resource usage (top  lines)\n"
        "/log - Recent activity (Admin only)\n\n"
        "<i>Note: /log access is restricted to authorized IDs.</i>"
    )
    await message.answer(help_text, parse_mode="HTML")
