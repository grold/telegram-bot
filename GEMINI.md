# Project: telegram-bot

## General Instructions

- When i ask for the functionality always use plan mode and ask follow up questions to clarify the requirements.
- Always unit test the functionality.
- Increase minor version on each commit or feature.
- For the new feature always create a new branch, and make a pull request after the feature is ready.
- analize errort through implementation of any feature and update GEMINI.md to prevent those next time

- **Technical Mandate:** Always ensure `ffmpeg` and local dependencies (like Whisper) are checked and handled gracefully in handlers.
- **Technical Mandate:** Use triple-quoted strings (`"""..."""`) for all multi-line strings and formatted responses to prevent syntax errors from accidental newlines.
- **Technical Mandate (Testing):** Always mock `aiogram` awaitable methods (like `message.answer`, `message.reply`, `bot.send_message`) using `AsyncMock` to avoid `TypeError`. Ensure all required attributes (e.g., `user.username`) are explicitly mocked.
- **Technical Mandate (Git):** When committing via `run_shell_command`, avoid using backticks (`` ` ``) or special shell characters in the commit message to prevent accidental execution errors.
- **Project Context:** This is a modular `aiogram 3` bot. New features should be added as separate routers in `handlers/` and registered in `bot.py`.

## Coding Style
- Use asynchronous patterns consistently.
- Prefer `FSInputFile` for local file delivery.
- Maintain comprehensive logging using the project's established `logger` patterns.

