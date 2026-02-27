import os
import asyncio
import logging
from aiogram import Router, types
from aiogram.filters import Command

router = Router()
logger = logging.getLogger(__name__)

LOG_FILE = "commands.log"
NUM_LINES = 10  # This could also be moved to config if needed, staying local for now as per previous refactor

def read_last_lines(filepath: str, num_lines: int) -> list[str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        # A simple readlines is fine for small/medium files.
        return f.readlines()[-num_lines:]

@router.message(Command("log"))
async def cmd_log(message: types.Message):
    """Sends the last configured number of lines of the commands.log file."""
    if not os.path.exists(LOG_FILE):
        await message.answer("Log file is currently empty or does not exist.")
        return

    try:
        from config import LOG_NUM_LINES
        last_lines = await asyncio.to_thread(read_last_lines, LOG_FILE, LOG_NUM_LINES)
        
        if not last_lines:
            await message.answer("Log file is empty.")
            return

        log_content = "".join(last_lines)
        
        # Telegram messages have a 4096 character limit.
        if len(log_content) > 4000:
            log_content = log_content[-4000:]
            
        from config import LOG_NUM_LINES
        await message.answer(f"<b>Last {min(len(last_lines), LOG_NUM_LINES)} Log Entries:</b>\n<pre>{log_content}</pre>", parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"Failed to read log file: {str(e)}")
