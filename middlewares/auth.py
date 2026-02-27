import os
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

logger = logging.getLogger(__name__)

AUTH_FILE = ".auth"

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

class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        authorized_users = get_authorized_users()
        if user.id not in authorized_users:
            logger.warning(f"Unauthorized access attempt to {event.text} from user ID: {user.id}")
            await event.answer("You are not authorized to use this command.")
            return

        return await handler(event, data)
