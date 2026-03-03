# Project: telegram-bot

## General Instructions

- When i ask for the functionality always use plan mode and ask follow up questions to clarify the requirements.
- Always unit test the functionality.
- Increase patch version in pyproject.toml after each commit or feature.
- For the new feature always create a new branch, and make a pull request after the feature is ready.
- analize error through implementation of any feature and update GEMINI.md to prevent those next time
- When i ask to release new version increase minor version in pyproject.toml and make a commit with a tag = version

- **Technical Mandate:** Always ensure `ffmpeg` and local dependencies (like Whisper) are checked and handled gracefully in handlers.
- **Technical Mandate:** Use triple-quoted strings (`"""..."""`) for all multi-line strings and formatted responses to prevent syntax errors from accidental newlines.
- **Technical Mandate (Testing):** Always mock `aiogram` awaitable methods (like `message.answer`, `message.reply`, `bot.send_message`) using `AsyncMock` to avoid `TypeError`. Ensure all required attributes (e.g., `user.username`) are explicitly mocked.
- **Technical Mandate (Git):** When committing via `run_shell_command`, avoid using backticks (`` ` ``) or special shell characters in the commit message to prevent accidental execution errors.
- **Technical Mandate (Architecture):** Use Middlewares for all passive data tracking (like location updates, interaction logging, etc.) instead of handlers to prevent "swallowing" of updates by competing routers.
- **Technical Mandate (Validation):** Always validate data retrieved from external sources (e.g., camera snapshots, weather APIs) before passing it to Telegram. Specifically, check that buffers/files are non-empty to avoid "Bad Request: file must be non-empty" errors.
- **Technical Mandate (Consistency):** Set global defaults (like `parse_mode="HTML"`) in `bot.py` via `DefaultBotProperties` rather than configuring them in individual handlers to prevent inconsistencies.
- **Technical Mandate (Compatibility):** When interacting with local hardware or legacy protocols (like ONVIF/Digest Auth), prioritize robust libraries (like `requests`) and wrap synchronous calls in `asyncio.to_thread` rather than using less-compatible async-native alternatives.
- **Technical Mandate (FFmpeg):** For RTSP streams, use `-timeout` (in microseconds) instead of `-stimeout` to ensure compatibility across demuxers. Always re-encode video for Telegram using `libx264`, `-pix_fmt yuv420p`, and `-movflags +faststart` to ensure cross-platform playback compatibility.
- **Technical Mandate (Testing):** When mocking functions that receive dynamic arguments (like timestamps or unique file paths), use `unittest.mock.ANY` in assertions to avoid fragile test failures.
- **Technical Mandate (Documentation):** Every new user-facing command must be documented in the `cmd_help` handler in `handlers/help.py`.
- **Technical Mandate (Git):** Always verify the repository's default branch name (using `git remote show origin` or `list_branches`) before creating a pull request to avoid 'invalid base' errors.
- **Project Context:** This is a modular `aiogram 3` bot. New features should be added as separate routers in `handlers/` and registered in `bot.py`.

## Coding Style
- Use asynchronous patterns consistently.
- Prefer `FSInputFile` for local file delivery.
- Maintain comprehensive logging using the project's established `logger` patterns.

