import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from database import (
    get_user, get_user_by_username, grant_user_access, 
    revoke_user_access, get_authorized_users_db, set_command_min_role
)

logger = logging.getLogger(__name__)
router = Router()

ROLES = ["USER", "ADMIN", "OWNER"]
ACCESS_LEVELS = ["PUBLIC", "USER", "ADMIN", "OWNER"]

@router.message(Command("grant"))
async def cmd_grant(message: types.Message, command: CommandObject, user_role: str):
    """Handles /grant @username [role] command."""
    if user_role not in ["ADMIN", "OWNER"]:
        return # AuthMiddleware should handle this, but double check

    args = command.args.split() if command.args else []
    if not args:
        await message.answer("Usage: <code>/grant @username [role]</code>\nRoles: USER, ADMIN, OWNER")
        return

    username = args[0]
    role = args[1].upper() if len(args) > 1 else "USER"

    if role not in ROLES:
        await message.answer(f"❌ Invalid role. Choose from: {', '.join(ROLES)}")
        return

    # Only OWNER can grant OWNER role
    if role == "OWNER" and user_role != "OWNER":
        logger.warning(f"Unauthorized grant attempt: User {message.from_user.id} ({user_role}) tried to grant OWNER role to {username}")
        await message.answer("❌ Only the <b>OWNER</b> can grant the <b>OWNER</b> role.")
        return

    user = get_user_by_username(username)
    if not user:
        logger.info(f"Grant attempt failed: User {username} not found in database")
        await message.answer(f"❌ User <b>{username}</b> not found in database. Ask them to /start first.")
        return

    grant_user_access(user["user_id"], role, username=username)
    await message.answer(f"✅ User <b>{username}</b> is now authorized with role <b>{role}</b>.")
    logger.info(f"RBAC: User {message.from_user.id} ({user_role}) GRANTED {role} to {username} ({user['user_id']})")

@router.message(Command("revoke"))
async def cmd_revoke(message: types.Message, command: CommandObject, user_role: str):
    """Handles /revoke @username command."""
    if user_role not in ["ADMIN", "OWNER"]:
        return

    args = command.args.split() if command.args else []
    if not args:
        await message.answer("Usage: <code>/revoke @username</code>")
        return

    username = args[0]
    user = get_user_by_username(username)
    if not user:
        await message.answer(f"❌ User <b>{username}</b> not found.")
        return

    # OWNER cannot be revoked by ADMIN
    if user["role"] == "OWNER" and user_role != "OWNER":
        logger.warning(f"Unauthorized revoke attempt: User {message.from_user.id} ({user_role}) tried to revoke OWNER {username}")
        await message.answer("❌ Only the <b>OWNER</b> can revoke another <b>OWNER</b>.")
        return

    revoke_user_access(user["user_id"])
    await message.answer(f"✅ User <b>{username}</b> access has been revoked.")
    logger.info(f"RBAC: User {message.from_user.id} ({user_role}) REVOKED access for {username} ({user['user_id']})")

@router.message(Command("list_authorized"))
async def cmd_list_authorized(message: types.Message, user_role: str):
    """Handles /list_authorized command."""
    if user_role not in ["ADMIN", "OWNER"]:
        return

    users = get_authorized_users_db()
    if not users:
        await message.answer("No authorized users found.")
        return

    text = "<b>Authorized Users:</b>\n"
    for user in users:
        username = f"@{user['username']}" if user['username'] else f"ID: {user['user_id']}"
        text += f"• {username} [<b>{user['role']}</b>]\n"
    
    await message.answer(text)

@router.message(Command("set_access"))
async def cmd_set_access(message: types.Message, command: CommandObject, user_role: str):
    """Handles /set_access [command] [level] command."""
    if user_role not in ["ADMIN", "OWNER"]:
        return

    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.answer("Usage: <code>/set_access [command] [PUBLIC|USER|ADMIN|OWNER]</code>")
        return

    cmd_to_set = args[0].lower().replace("/", "")
    level = args[1].upper()

    if level not in ACCESS_LEVELS:
        await message.answer(f"❌ Invalid level. Choose from: {', '.join(ACCESS_LEVELS)}")
        return

    set_command_min_role(cmd_to_set, level)
    await message.answer(f"✅ Access for <code>/{cmd_to_set}</code> set to <b>{level}</b>.")
    logger.info(f"RBAC: User {message.from_user.id} ({user_role}) set /{cmd_to_set} access level to {level}")
