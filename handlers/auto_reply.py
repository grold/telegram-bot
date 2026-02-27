from aiogram import Router, F, types

router = Router()

AUTO_REPLIES = {
    "hello": "Hi there! How can I assist you?",
    "pricing": "Our pricing details can be found on our website: example.com/pricing",
    "support": "You can contact support at support@example.com",
}

@router.message(F.text)
async def auto_reply(message: types.Message):
    text = message.text.lower()
    for keyword, reply in AUTO_REPLIES.items():
        if keyword in text:
            await message.reply(reply)
            return
