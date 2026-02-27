from aiogram import Router, F, types
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER

router = Router()
router.message.filter(F.chat.type.in_({"group", "supergroup"}))

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: types.ChatMemberUpdated):
    await event.answer(f"Welcome to the group, {event.new_chat_member.user.first_name}!")

@router.message(F.new_chat_members)
async def on_user_join_message(message: types.Message):
    for user in message.new_chat_members:
        await message.answer(f"Welcome, {user.first_name}!")
