import logging
import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from database import get_known_groups

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("mygroups"))
async def cmd_mygroups(message: types.Message):
    """Handles the /mygroups command to list groups the bot has interacted with."""
    try:
        groups = await asyncio.to_thread(get_known_groups)
        
        if not groups:
            await message.answer("No known groups found in logs.")
            return

        response_lines = ["<b>📂 Known Groups:</b>\n"]
        for group in groups:
            chat_id = group['chat_id']
            title = group['chat_title'] or "Unknown Title"
            last_seen = group['last_seen']
            
            response_lines.append(f"• <b>{title}</b> (ID: <code>{chat_id}</code>)\n  Last seen: {last_seen}")

        # Join lines and handle potential message length limit (simple check)
        response_text = "\n".join(response_lines)
        if len(response_text) > 4000:
             # Basic truncation if too long
            response_text = response_text[:4000] + "..."

        await message.answer(response_text)
    
    except Exception as e:
        logger.error(f"Error in cmd_mygroups: {e}")
        await message.answer(f"Error retrieving groups: {str(e)}")
