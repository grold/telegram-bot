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
        "<b>📍 Circle of Friends:</b>\n"
        "/share [on|off|update|status] - Manage location sharing\n"
        "/map [list|username] - See mutual friends on a map\n"
        "<b>📸 Camera:</b>\n"
        "/camera screenshot - Capture a snapshot from local camera\n"
        "<b>🛡️ Admin Commands:</b>\n"
        "/photo - Send a random photo\n"
        "/top - Server resource usage\n"
        "/log - Recent activity\n\n"
        "<i>Note: Admin commands are restricted to authorized IDs in .auth.</i>\n\n"
        "📦 <b>GitHub:</b> https://github.com/grold/telegram-bot"
    )
    await message.answer(help_text)
