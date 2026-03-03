import asyncio
import logging
from aiogram import Router, types
from aiogram.filters import Command
from config import LOG_NUM_LINES
from database import get_recent_logs

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("log"))
async def cmd_log(message: types.Message):
    """Sends the last configured number of lines of the interaction logs from SQLite."""
    try:
        # Fetch logs from DB in a thread to keep it async friendly
        logs = await asyncio.to_thread(get_recent_logs, LOG_NUM_LINES)
        
        if not logs:
            await message.answer("Log database is empty.")
            return

        # Format log entries for Telegram
        # Format: [Time] User: Content (Duration)
        formatted_entries = []
        for log in logs:
            # Shorten timestamp for display: 2024-03-03 13:28:11 -> 13:28:11
            time_str = log['timestamp'].split()[-1] if ' ' in log['timestamp'] else log['timestamp']
            user_display = f"@{log['username']}" if log['username'] else log['full_name']
            
            entry = (
                f"<code>[{time_str}]</code> <b>{user_display}</b>: "
                f"<i>{log['content']}</i> ({log['duration_ms']:.1f}ms)"
            )
            formatted_entries.append(entry)
            
        # Reverse to show chronological order like a text file tail
        formatted_entries.reverse()
        log_content = "\n".join(formatted_entries)
        
        # Telegram messages have a 4096 character limit.
        if len(log_content) > 4000:
            log_content = log_content[-4000:]
            
        await message.answer(
            f"<b>Last {len(logs)} Interaction Logs:</b>\n\n{log_content}", 
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.exception("Failed to read logs from database")
        await message.answer(f"Failed to read log database: {str(e)}")
