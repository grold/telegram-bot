import logging
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllChatAdministrators, BotCommandScopeChat
from database import get_all_commands, get_user
from middlewares.auth import ROLES_ORDER

logger = logging.getLogger(__name__)

async def sync_bot_commands(bot: Bot, user_id: int = None):
    """
    Synchronizes bot commands with Telegram based on RBAC roles.
    If user_id is provided, sets commands for that specific chat (private).
    If user_id is None, sets global scopes (Default and AllChatAdministrators).
    """
    try:
        db_commands = get_all_commands()
        if not db_commands:
            logger.warning("No commands found in database for synchronization.")
            return

        # Sort commands by name for consistency
        db_commands = sorted(db_commands, key=lambda x: x["command"])

        if user_id:
            user = get_user(user_id)
            user_role = user["role"] if user and user["is_authorized"] else "PUBLIC"
            user_level = ROLES_ORDER.get(user_role, 0)
            
            visible_commands = [
                BotCommand(command=cmd["command"], description=cmd["description"] or cmd["command"])
                for cmd in db_commands
                if cmd["is_visible"] and ROLES_ORDER.get(cmd["min_role"], 0) <= user_level
            ]
            
            # Telegram Bot API: set_bot_commands with empty list clears commands for the scope
            await bot.set_bot_commands(visible_commands, scope=BotCommandScopeChat(chat_id=user_id))
            logger.info(f"Synchronized commands for user {user_id} (Role: {user_role}, Count: {len(visible_commands)})")
        else:
            # Global scopes
            # 1. Default (Public) - Show to everyone
            public_commands = [
                BotCommand(command=cmd["command"], description=cmd["description"] or cmd["command"])
                for cmd in db_commands
                if cmd["is_visible"] and cmd["min_role"] == "PUBLIC"
            ]
            await bot.set_bot_commands(public_commands, scope=BotCommandScopeDefault())
            logger.info(f"Synchronized global PUBLIC commands ({len(public_commands)} commands).")

            # 2. All Chat Administrators (Admins) - Show PUBLIC + USER + ADMIN
            admin_level = ROLES_ORDER.get("ADMIN", 2)
            admin_commands = [
                BotCommand(command=cmd["command"], description=cmd["description"] or cmd["command"])
                for cmd in db_commands
                if cmd["is_visible"] and ROLES_ORDER.get(cmd["min_role"], 0) <= admin_level
            ]
            await bot.set_bot_commands(admin_commands, scope=BotCommandScopeAllChatAdministrators())
            logger.info(f"Synchronized global ADMIN commands ({len(admin_commands)} commands).")
            
    except Exception as e:
        logger.error(f"Failed to synchronize bot commands: {e}", exc_info=True)
