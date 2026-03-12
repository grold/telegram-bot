import asyncio
import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from config import LOG_NUM_LINES
from database import get_recent_logs

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("log"))
async def cmd_log(message: types.Message, command: CommandObject, user_role: str):
    """Sends the last configured number of lines of the interaction logs with optional filtering."""
    try:
        # Parse arguments: /log [num] [query]
        args = command.args.split() if command.args else []
        limit = LOG_NUM_LINES
        query = None

        if args:
            if args[0].isdigit():
                limit = int(args[0])
                if len(args) > 1:
                    query = " ".join(args[1:])
            else:
                query = " ".join(args)

        # Fetch logs from DB
        logs = await asyncio.to_thread(get_recent_logs, limit, query)

        if not logs:
            msg = f"Log database is empty for query: '{query}'" if query else "Log database is empty."
            await message.answer(msg)
            return

        # Format log entries for Telegram
        formatted_entries = []
        for log in logs:
            time_str = log['timestamp']
            user_display = f"@{log['username']}" if log['username'] else log['full_name']
            
            # sqlite3.Row doesn't support .get(), check if column exists and is not None
            user_role_val = None
            if 'user_role' in log.keys():
                user_role_val = log['user_role']
            
            role_display = f" [🛡️ {user_role_val}]" if user_role_val else ""
            chat_display = f" | 💬 {log['chat_title']}" if log['chat_title'] else ""
            bot_ver = f" [🤖 {log['bot_version']}]" if log['bot_version'] else ""

            entry = (
                f"<b>📅 {time_str} | 👤 {user_display}{role_display}{chat_display}</b>\n"
                f"📝 <i>{log['content']}</i> ({log['duration_ms']:.1f}ms){bot_ver}"
            )
            formatted_entries.append(entry)

        # Reverse to show chronological order like a text file tail
        formatted_entries.reverse()

        header = f"<b>Last {len(logs)} Interaction Logs"
        if query:
            header += f" matching '{query}'"
        header += ":</b>\n\n"

        log_content = "\n---\n".join(formatted_entries)

        # Telegram messages have a 4096 character limit.
        full_msg = f"{header}{log_content}"
        if len(full_msg) > 4000:
            # If too long, we might need to truncate entries or send multiple messages.
            # For now, just truncate from the beginning (oldest) to keep newest.
            full_msg = full_msg[-4000:]
            if not full_msg.startswith("<b>"):
                full_msg = "... " + full_msg

        await message.answer(full_msg, parse_mode="HTML")

    except Exception as e:
        logger.exception("Failed to read logs from database")
        await message.answer(f"Failed to read log database: {str(e)}")
