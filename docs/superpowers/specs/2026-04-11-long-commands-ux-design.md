# Design Spec: Enhanced UX for Long-Running Commands

**Date:** 2026-04-11
**Topic:** long-commands-ux

## Overview
Improve user experience during long-running bot operations (audio transcription, weather analysis via EXIF, and camera capture) by using Telegram's "Chat Actions" and implementing real-time streaming for transcription.

## Goals
1. Provide immediate visual feedback to the user that the bot is "working" using `sendChatAction`.
2. Reduce perceived latency for audio transcription by streaming text as it is generated.

## Architecture & Components

### 1. `ChatActionSender` Integration
Utilize `aiogram.utils.chat_action.ChatActionSender` as an asynchronous context manager in relevant handlers.

- **Audio (`handle_audio_message`)**: `ChatAction.TYPING`
- **Exif Weather (`process_photo_for_exif`)**: `ChatAction.FIND_LOCATION`
- **Camera (`cmd_camera`)**:
  - Screenshot: `ChatAction.UPLOAD_PHOTO`
  - Video: `ChatAction.UPLOAD_VIDEO`

### 2. Streaming Transcription (`sendMessageDraft`)
Transition `handlers/audio.py` from the high-level `pipeline` to low-level `model.generate`.

- **`TelegramStreamer`**: A custom class inheriting from `transformers.BaseStreamer`.
  - **Logic**: Collects tokens, decodes them to text, and periodically updates a "draft" message in Telegram.
  - **Throttling**: Updates the message every ~1.5 seconds to avoid Telegram's rate limits.
  - **Fallback**: If streaming fails or the message is deleted, it will fall back to sending the full result at the end.

### 3. Data Flow (Audio)
1. User sends audio/voice.
2. Bot starts `ChatActionSender(action="typing")`.
3. Bot sends an initial "draft" message: `msg = await message.reply("🎤 Transcribing...")`.
4. Audio is loaded and processed via `processor`.
5. `model.generate` is called with `streamer=TelegramStreamer(msg)`.
6. As tokens arrive, `msg.edit_text` is called with accumulated text.
7. Final transcription is saved to a file and sent as a final reply with full formatting.

## Error Handling
- If `sendChatAction` fails, it should not crash the handler (standard `ChatActionSender` behavior).
- If `edit_text` for streaming fails (e.g., message deleted by user), the streamer should stop updating but the main transcription should continue.

## Testing Strategy
- **Unit Tests**:
  - Mock `ChatActionSender` to verify it's called with the correct action.
  - Mock `TelegramStreamer` to verify it correctly accumulates tokens and calls `edit_text` with throttling.
- **Integration Tests**:
  - Test the full flow of `/camera` and audio transcription with mocked Telegram API responses.

## Success Criteria
- Bot shows correct status (typing, uploading, etc.) during all long operations.
- Audio transcription shows partial results in the chat before the final message.
- No "Rate limit exceeded" errors from Telegram during streaming.
