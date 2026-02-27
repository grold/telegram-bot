import subprocess
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    try:
        # Run top in batch mode, 1 iteration
        output = subprocess.check_output(["top", "-b", "-n", "1"]).decode("utf-8")
        # Take the first 12 lines to keep the message concise
        summary = "\n".join(output.splitlines()[:12])
        await message.answer(f"<code>{summary}</code>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Error getting system info: {str(e)}")
