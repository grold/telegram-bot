# Long-Running Commands UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve UX for long-running commands using `sendChatAction` and streaming transcription.

**Architecture:** 
- Integrate `ChatActionSender` into audio, EXIF weather, and camera handlers.
- Refactor `handlers/audio.py` to use low-level Whisper inference with a custom `TelegramStreamer`.
- Throttled message updates to respect Telegram rate limits.

**Tech Stack:** `aiogram 3`, `transformers`, `optimum[openvino]`.

---

### Task 1: Basic `sendChatAction` Integration

**Files:**
- Modify: `handlers/exif_weather.py`
- Modify: `handlers/camera.py`

- [ ] **Step 1: Add `ChatActionSender` to EXIF weather**

Modify `handlers/exif_weather.py`:
```python
from aiogram.utils.chat_action import ChatActionSender
from aiogram.enums import ChatAction

# In process_photo_for_exif:
async with ChatActionSender.find_location(bot=bot, chat_id=message.chat.id):
    # Existing logic...
```

- [ ] **Step 2: Add `ChatActionSender` to Camera Screenshot**

Modify `handlers/camera.py`:
```python
# In cmd_camera (screenshot part):
async with ChatActionSender.upload_photo(bot=message.bot, chat_id=message.chat.id):
    # Existing logic...
```

- [ ] **Step 3: Add `ChatActionSender` to Camera Video**

Modify `handlers/camera.py`:
```python
# In cmd_camera (video part):
async with ChatActionSender.upload_video(bot=message.bot, chat_id=message.chat.id):
    # Existing logic...
```

- [ ] **Step 4: Commit**
```bash
git add handlers/exif_weather.py handlers/camera.py
git commit -m "ux: add ChatActionSender to EXIF weather and camera handlers"
```

---

### Task 2: Refactor Audio Handler for Streaming (Preparation)

**Files:**
- Modify: `handlers/audio.py`

- [ ] **Step 1: Update Imports and Global Model Loading**

Modify `handlers/audio.py` to expose `model` and `processor` separately.

- [ ] **Step 2: Implement `TelegramStreamer`**

```python
import time
from transformers import BaseStreamer

class TelegramStreamer(BaseStreamer):
    def __init__(self, message, processor, interval=1.5):
        self.message = message
        self.processor = processor
        self.interval = interval
        self.last_update = 0
        self.tokens = []
        self.text = ""

    def put(self, value):
        self.tokens.append(value.tolist()[0])
        if time.time() - self.last_update > self.interval:
            self.update_message()

    def end(self):
        self.update_message()

    def update_message(self):
        new_text = self.processor.batch_decode(self.tokens, skip_special_tokens=True)[0]
        if new_text.strip() != self.text.strip():
            self.text = new_text
            asyncio.create_task(self.message.edit_text(f"🎤 {self.text}..."))
            self.last_update = time.time()
```

- [ ] **Step 3: Commit**
```bash
git add handlers/audio.py
git commit -m "ux: implement TelegramStreamer for audio transcription"
```

---

### Task 3: Implement Low-Level Streaming Inference

**Files:**
- Modify: `handlers/audio.py`

- [ ] **Step 1: Replace `pipe(audio_data)` with `model.generate`**

Modify `handle_audio_message` to use the new streamer and `ChatActionSender`.

- [ ] **Step 2: Commit**
```bash
git add handlers/audio.py
git commit -m "ux: switch to low-level streaming inference for audio"
```

---

### Task 4: Testing & Validation

- [ ] **Step 1: Update Tests**
- [ ] **Step 2: Verify with Mock AIogram**
- [ ] **Step 3: Commit**

---

### Task 5: Version Bump

- [ ] **Step 1: Update `pyproject.toml`**
- [ ] **Step 2: Update `VERSION.md`**
- [ ] **Step 3: Commit**
