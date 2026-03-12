import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
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
    """Handles /list_authorized command with interactive buttons."""
    if user_role not in ["ADMIN", "OWNER"]:
        return

    users = get_authorized_users_db()
    if not users:
        await message.answer("No authorized users found.")
        return

    await message.answer("<b>Authorized Users Management:</b>")
    
    for user in users:
        username = f"@{user['username']}" if user['username'] else f"ID: {user['user_id']}"
        text = f"👤 {username} [<b>{user['role']}</b>]"
        
        builder = InlineKeyboardBuilder()
        # Callback data format: action:user_id
        builder.button(text="📝 Edit Role", callback_data=f"auth_role:{user['user_id']}")
        builder.button(text="❌ Revoke", callback_data=f"auth_revoke:{user['user_id']}")
        builder.adjust(2)
        
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("auth_role:"))
async def cb_auth_role(callback: types.CallbackQuery, user_role: str):
    """Shows role selection buttons for a user."""
    if user_role not in ["ADMIN", "OWNER"]:
        await callback.answer("Unauthorized.", show_alert=True)
        return

    target_id = int(callback.data.split(":")[1])
    target_user = get_user(target_id)
    
    if not target_user:
        await callback.answer("User not found.")
        return

    # Check permissions
    if target_user["role"] == "OWNER" and user_role != "OWNER":
        await callback.answer("Only OWNER can change OWNER's role.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for role in ROLES:
        # Don't show current role
        if role == target_user["role"]:
            continue
        # Only OWNER can grant OWNER
        if role == "OWNER" and user_role != "OWNER":
            continue
            
        builder.button(text=f"Set to {role}", callback_data=f"auth_set:{target_id}:{role}")
    
    builder.button(text="🔙 Back", callback_data=f"auth_back:{target_id}")
    builder.adjust(1)
    
    username = f"@{target_user['username']}" if target_user['username'] else f"ID: {target_id}"
    await callback.message.edit_text(
        f"Change role for {username} (Current: {target_user['role']}):",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("auth_set:"))
async def cb_auth_set(callback: types.CallbackQuery, user_role: str):
    """Applies a new role to a user."""
    if user_role not in ["ADMIN", "OWNER"]:
        return

    _, target_id, new_role = callback.data.split(":")
    target_id = int(target_id)
    
    target_user = get_user(target_id)
    if not target_user:
        await callback.answer("User not found.")
        return

    # Security checks
    if new_role == "OWNER" and user_role != "OWNER":
        await callback.answer("Only OWNER can grant OWNER role.", show_alert=True)
        return
    if target_user["role"] == "OWNER" and user_role != "OWNER":
        await callback.answer("Only OWNER can modify an OWNER.", show_alert=True)
        return

    grant_user_access(target_id, new_role)
    logger.info(f"RBAC: User {callback.from_user.id} ({user_role}) changed {target_id} role to {new_role} via UI")
    
    await callback.answer(f"Success! Role set to {new_role}")
    await cb_auth_back(callback, user_role)

@router.callback_query(F.data.startswith("auth_revoke:"))
async def cb_auth_revoke(callback: types.CallbackQuery, user_role: str):
    """Revokes a user's access."""
    if user_role not in ["ADMIN", "OWNER"]:
        return

    target_id = int(callback.data.split(":")[1])
    target_user = get_user(target_id)
    
    if not target_user:
        await callback.answer("User not found.")
        return

    if target_user["role"] == "OWNER" and user_role != "OWNER":
        await callback.answer("Only OWNER can revoke an OWNER.", show_alert=True)
        return

    revoke_user_access(target_id)
    logger.info(f"RBAC: User {callback.from_user.id} ({user_role}) REVOKED {target_id} via UI")
    
    await callback.answer("Access revoked.")
    await callback.message.delete()

@router.callback_query(F.data.startswith("auth_back:"))
async def cb_auth_back(callback: types.CallbackQuery, user_role: str):
    """Returns to the user entry view."""
    target_id = int(callback.data.split(":")[1])
    target_user = get_user(target_id)
    
    if not target_user or not target_user["is_authorized"]:
        await callback.message.delete()
        return

    username = f"@{target_user['username']}" if target_user['username'] else f"ID: {target_user['user_id']}"
    text = f"👤 {username} [<b>{target_user['role']}</b>]"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Edit Role", callback_data=f"auth_role:{target_user['user_id']}")
    builder.button(text="❌ Revoke", callback_data=f"auth_revoke:{target_user['user_id']}")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()

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
