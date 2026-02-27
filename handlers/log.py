import os
import asyncio
import logging
from aiogram import Router, types
from aiogram.filters import Command

router = Router()
logger = logging.getLogger(__name__)

AUTH_FILE = ".auth"

LOG_FILE = "commands.log"
NUM_LINES = 30

def read_last_lines(filepath: str, num_lines: int) -> list[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        # A simple readlines is fine for small/medium files.
        return f.readlines()[-num_lines:]

def get_authorized_users() -> set[int]:
    """Reads the authorized user IDs from the .auth file."""
    if not os.path.exists(AUTH_FILE):
        return set()
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return {int(line.strip()) for line in f if line.strip().isdigit()}
    except Exception as e:
        logger.error(f"Error reading {AUTH_FILE}: {e}")
        return set()

@router.message(Command("log"))
async def cmd_log(message: types.Message):
    """Sends the last 30 lines of the commands.log file."""
    authorized_users = get_authorized_users()
    
    if message.from_user.id not in authorized_users:
        logger.warning(f"Unauthorized access attempt to /log command from user ID: {message.from_user.id}")
        await message.answer("You are not authorized to use this command.")
        return
    if not os.path.exists(LOG_FILE):
        await message.answer("Log file is currently empty or does not exist.")
        return

    try:
        last_lines = await asyncio.to_thread(read_last_lines, LOG_FILE, NUM_LINES)
        
        if not last_lines:
            await message.answer("Log file is empty.")
            return

        log_content = "".join(last_lines)
        
        # Telegram messages have a 4096 character limit.
        if len(log_content) > 4000:
            log_content = log_content[-4000:]
            
        await message.answer(f"<b>Last {min(len(last_lines), NUM_LINES)} Log Entries:</b>\n<pre>{log_content}</pre>", parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"Failed to read log file: {str(e)}")
