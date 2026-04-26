# Version History

## Version 0.7.5 (2026-04-26)

### New Features & Improvements
- **Coolify Deployment Setup**: Added a `Dockerfile` and `.dockerignore` for deploying to Coolify.
- **Finalized Optimization Summary**:
    - **Python 3.13**: Switched back from 3.14 to ensure pre-compiled binaries (wheels) are available for most libraries, significantly speeding up the build.
    - **CPU-Only Torch**: Added `UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu` to skip downloading ~2GB of NVIDIA CUDA libraries since you are using Intel Iris Graphics.

## Version 0.7.2 (2026-04-11)

### New Features
- **Enhanced UX for Long Commands**: Integrated `sendChatAction` to provide immediate visual feedback for long-running operations.
    - **Audio Transcription**: Shows "typing..." status.
    - **EXIF Weather**: Shows "finding location..." status.
    - **Camera Capture**: Shows "uploading photo/video..." status.
- **Streaming Audio Transcription**: Refactored the audio handler to stream transcription text as it is generated using a custom `TelegramStreamer`.
    - Uses low-level `model.generate` for token-by-token generation.
    - Throttled Telegram message updates (every 1.5s) to respect rate limits.

### Improvements & Bug Fixes
- **Refactoring**: Transitioned from high-level Whisper pipeline to low-level inference for better control.
- **Testing**: Added specialized test suites for `ChatActionSender` and `TelegramStreamer`.

## Version 0.7.1 (2026-04-10)

### New Features
- **EXIF Weather Analysis**: Added capability to analyze photo metadata (EXIF) to fetch historical weather for the location and time the photo was taken.
    - Automatically extracts GPS coordinates and timestamps from uploaded photos.
    - Integrates with Open-Meteo Historical API for precise weather reports.

## Version 0.7.0 (2026-04-02)

### New Features
- **Lazy Loading for Whisper**: Transcription model now only loads when the first voice/audio message is received.
    - Improved bot startup time (deferred heavy AI module loading).
    - Uses `asyncio.to_thread` for non-blocking initialization on first use.
    - Added user feedback with "⏳ Loading..." status messages.
- **Enhanced Error Reporting**: Complete integration of exception tracking into the bot's middleware.
    - Automatically captures, logs, and re-raises all handler exceptions.
    - Saves full tracebacks to the database for remote debugging.
    - Added visual success (✅) and failure (❌) markers to the `/log` output.
    - Added `/log errors` filter for rapid incident triage.

### Improvements & Bug Fixes
- **Testing**: Added specialized test suites for lazy loading (`test_audio_lazy_loading.py`) and error logging (`test_error_logging.py`).
- **Stability**: Refactored `InteractionLoggingMiddleware` for better asynchronous performance and reliability.
- **Documentation**: Updated `README.md` and `GEMINI.md` to reflect new architecture and technical mandates.

## Version 0.6.3 (2026-04-01)
- Minor documentation and design preparation for lazy loading features.

## Version 0.6.2 (2026-03-25)

### New Features
- **Enhanced Error Reporting**: Integrated robust error capturing into the bot's logging middleware.
    - All handler exceptions are now caught, logged to the database with full traceback, and then re-raised.
    - Added visual indicators (✅/❌) to the `/log` command.
    - Added a `/log errors` filter to quickly view failed interactions.

### Improvements & Bug Fixes
- **Testing**: Fixed regression tests for `mygroups`, `time`, and `audio` handlers to align with recent RBAC and global bot property changes.
- **Database**: Added `status`, `exception`, and `traceback` columns to the `logs` table with automatic migration.

## Version 0.6.0 (2026-03-12)

### New Features
- **Windy Webcams (`/webcams`)**: Integrated Windy API v3 to explore and view live webcams globally.
    - Search by city, country, category, or nearby location.
    - Support for live/timelapse player links and preview images.
- **Admin Group Management (`/mygroups`)**: New admin command to monitor groups where the bot is present.
    - Includes clickable invite links for easier navigation.
    - Tracks "first seen" timestamps for each group.

### Improvements & Bug Fixes
- **Refactoring**: Improved internal router registration and middleware handling.
- **Documentation**: Renamed `version.md` to `VERSION.md` for consistency.
- **Testing**: Added comprehensive test suite for the new `/webcams` functionality.

---

## Version 0.5.0 (2026-03-09)

### New Features
- **Whisper GPU Acceleration**: Enabled Intel Iris Graphics acceleration via OpenVINO for significantly faster audio transcription.
- **Enhanced Camera Screenshots**: Added a comprehensive weather overlay for Izhevsk on camera snapshots.
- **Refactored Currency Rates (`/rate`)**: Completely redesigned to support dynamic currency pairs.
- **Enriched Logging (`/log`)**: Enhanced command with filtering by log level and result limits.

### Improvements & Bug Fixes
- **Audio Transcription**: Added support for very long voice messages using the Whisper pipeline with automatic chunking.
- **Stability**: Added `intel-opencl-icd` check and better handling of hardware-specific optimizations.

---

## Version 0.4.0 (2026-03-04)

### New Features
- **Exchange Rates (`/rate`)**: Initial implementation to fetch current exchange rates for USD, EUR, and JPY against RUB.
- **Camera Video (`/camera video`)**: Implemented ability to record short video clips from ONVIF cameras.

---

## Version 0.3.0 (2026-03-03)

### New Features
- **Core Commands**: Implemented initial set of commands: `/time`, `/photo`, `/help`, and group management.
- **Logging System**: Added comprehensive command logging via middleware.
- **Admin Tools**: `/log`, `/top`, and others.
