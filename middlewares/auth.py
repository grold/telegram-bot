import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from database import get_user, ensure_user, get_command_min_role
from config import OWNER_ID

logger = logging.getLogger(__name__)

# Roles hierarchy
ROLES_ORDER = {
    "PUBLIC": 0,
    "USER": 1,
    "ADMIN": 2,
    "OWNER": 3
}

# Default permissions for specific commands (historically protected)
LEGACY_PROTECTED_COMMANDS = {
    "log": "ADMIN",
    "photo": "ADMIN",
    "top": "ADMIN",
    "mygroups": "ADMIN"
}

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_info = event.from_user
        if not user_info:
            return await handler(event, data)

        # 1. Ensure user exists and get their role
        ensure_user(user_info.id, user_info.username, user_info.full_name)
        user = get_user(user_info.id)
        
        # Hardcoded master owner from config takes precedence
        if user_info.id == OWNER_ID:
            user_role = "OWNER"
            is_authorized = True
        else:
            user_role = user["role"] if user and user["is_authorized"] else "PUBLIC"
            is_authorized = bool(user and user["is_authorized"])
        
        data["user_role"] = user_role
        data["is_authorized"] = is_authorized

        # 2. Determine required role for the command
        command_name = None
        if event.text and event.text.startswith("/"):
            command_name = event.text.split()[0][1:].split("@")[0].lower()

        if not command_name:
            return await handler(event, data)

        # Priority: DB settings -> Legacy defaults -> PUBLIC (default for others)
        min_role = get_command_min_role(command_name)
        if not min_role:
            min_role = LEGACY_PROTECTED_COMMANDS.get(command_name, "PUBLIC")
        
        # 3. Enforcement
        user_level = ROLES_ORDER.get(user_role, 0)
        required_level = ROLES_ORDER.get(min_role, 0)

        if user_level < required_level:
            logger.warning(
                f"Access denied: User {user_info.id} ({user_role}) tried {command_name} (needs {min_role})"
            )
            await event.answer(
                f"❌ Access denied. This command requires <b>{min_role}</b> level permissions."
            )
            return

        return await handler(event, data)
