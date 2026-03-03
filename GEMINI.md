# Project: telegram-bot

## General Instructions

- When i ask for the functionality always use plan mode and ask follow up questions to clarify the requirements.
- Always unit test the functionality.
- **Technical Mandate:** Always ensure `ffmpeg` and local dependencies (like Whisper) are checked and handled gracefully in handlers.
- **Project Context:** This is a modular `aiogram 3` bot. New features should be added as separate routers in `handlers/` and registered in `bot.py`.

## Coding Style
- Use asynchronous patterns consistently.
- Prefer `FSInputFile` for local file delivery.
- Maintain comprehensive logging using the project's established `logger` patterns.

