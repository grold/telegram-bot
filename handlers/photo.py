import os
import random
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

router = Router()

PHOTO_DIR = "photos"

@router.message(Command("photo"))
async def cmd_photo(message: types.Message):
    if not os.path.exists(PHOTO_DIR):
        await message.answer("Photo directory does not exist.")
        return

    photos = [f for f in os.listdir(PHOTO_DIR) if os.path.isfile(os.path.join(PHOTO_DIR, f))]
    
    if not photos:
        await message.answer("The photo folder is empty.")
        return

    random_photo = random.choice(photos)
    photo_path = os.path.join(PHOTO_DIR, random_photo)
    
    try:
        photo_file = FSInputFile(photo_path)
        await message.answer_photo(photo_file, caption=f"Here is a random photo: {random_photo}")
    except Exception as e:
        await message.answer(f"Failed to send photo: {str(e)}")
