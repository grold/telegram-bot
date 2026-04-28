from aiogram import Router, types
from aiogram.filters import Command
from config import BOT_VERSION
from database import get_all_commands
from middlewares.auth import ROLES_ORDER

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message, user_role: str = "PUBLIC"):
    db_commands = get_all_commands()
    user_level = ROLES_ORDER.get(user_role, 0)
    
    # Filter and format commands based on user role
    available_cmds = []
    for cmd in db_commands:
        if cmd["is_visible"] and ROLES_ORDER.get(cmd["min_role"], 0) <= user_level:
            desc = cmd["description"] or ""
            available_cmds.append(f"/{cmd['command']} - {desc}")
    
    available_cmds.sort()
    commands_text = "\n".join(available_cmds) if available_cmds else "No commands available for your role."

    help_text = (
        f"<b>🤖 Bot Version:</b> <code>{BOT_VERSION}</code>\n\n"
        "<b>✨ Inline Mode</b>\n"
        "Type <code>@groldtestbot [city]</code> in any chat for quick weather. "
        "Try <code>@groldtestbot</code> without text to use your current location!\n\n"
        "<b>🛠️ Available Commands:</b>\n"
        f"{commands_text}\n\n"
        "<b>📸 Photo Weather:</b>\n"
        "Send a <b>Photo</b> or <b>File</b> with GPS EXIF data to get historical weather!\n\n"
        "<i>Note: Protected commands require appropriate authorization levels.</i>\n\n"
        "📦 <b>GitHub:</b> https://github.com/grold/telegram-bot"
    )
    await message.answer(help_text)
