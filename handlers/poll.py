import os
import json
import logging
from aiogram import Router, types, Bot
from aiogram.filters import Command

router = Router()
logger = logging.getLogger(__name__)

POLLS_STORAGE = "active_polls.json"

def load_polls():
    if os.path.exists(POLLS_STORAGE):
        try:
            with open(POLLS_STORAGE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading polls: {e}")
    return {}

def save_poll(poll_id: str, chat_id: int):
    polls = load_polls()
    polls[poll_id] = chat_id
    try:
        with open(POLLS_STORAGE, "w") as f:
            json.dump(polls, f)
    except Exception as e:
        logger.error(f"Error saving poll: {e}")

def remove_poll(poll_id: str):
    polls = load_polls()
    if poll_id in polls:
        del polls[poll_id]
        try:
            with open(POLLS_STORAGE, "w") as f:
                json.dump(polls, f)
        except Exception as e:
            logger.error(f"Error removing poll: {e}")

@router.message(Command("poll_delete"))
async def cmd_poll_delete(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("This command can only be used in groups.")
        return

    poll_message = await message.answer_poll(
        question="Delete the bot from the group?",
        options=["Yes", "No"],
        type="regular",
        is_anonymous=False,
        open_period=21600, # 6 hours
    )
    
    save_poll(poll_message.poll.id, message.chat.id)
    logger.info(f"Started deletion poll {poll_message.poll.id} in chat {message.chat.id}")

@router.poll()
async def handle_poll_update(poll: types.Poll, bot: Bot):
    # This handler triggers whenever the poll status changes (including when it closes)
    if not poll.is_closed:
        return

    polls = load_polls()
    chat_id = polls.get(poll.id)
    
    if not chat_id:
        return

    # Process results
    results = {option.text: option.voter_count for option in poll.options}
    yes_votes = results.get("Yes", 0)
    no_votes = results.get("No", 0)
    
    result_text = (
        "📊 <b>Deletion Poll Results:</b>\n\n"
        f"✅ Yes: {yes_votes}\n"
        f"❌ No: {no_votes}\n\n"
    )

    if yes_votes > no_votes:
        result_text += "The majority voted <b>Yes</b>. I will now leave the group. Goodbye! 👋"
        try:
            await bot.send_message(chat_id, result_text, parse_mode="HTML")
            await bot.leave_chat(chat_id)
        except Exception as e:
            logger.error(f"Error leaving chat {chat_id}: {e}")
    else:
        result_text += "The majority voted <b>No</b>. I'm staying! 😊"
        try:
            await bot.send_message(chat_id, result_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error sending results to chat {chat_id}: {e}")

    remove_poll(poll.id)
