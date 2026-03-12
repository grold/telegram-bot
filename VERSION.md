# Version History

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
    - Uses `optimum-intel` backend.
    - Improved transcription reliability with chunking for long audio files.
- **Enhanced Camera Screenshots**: Added a comprehensive weather overlay for Izhevsk on camera snapshots.
    - Includes Temperature, "Feels Like," Condition, Humidity, and Wind speed.
    - Features a semi-transparent, multi-line overlay for maximum readability.
    - Configurable font path via `FONT_PATH` in `config.py`.
- **Refactored Currency Rates (`/rate`)**: Completely redesigned to support dynamic currency pairs (e.g., `/rate USD EUR`, `/rate BTC USD`).
    - Switched to a more flexible international API.
    - Added support for 150+ fiat currencies and major cryptocurrencies.
- **Enriched Logging (`/log`)**: Enhanced command for better bot monitoring.
    - Added filtering by log level (e.g., `/log error`).
    - Added configurable result limits (e.g., `/log 20`).
    - Improved output formatting with HTML blocks.

### Improvements & Bug Fixes
- **Audio Transcription**: Added support for very long voice messages using the Whisper pipeline with automatic chunking.
- **Dependencies**: Added `Pillow` for image processing and `httpx` for modern async HTTP requests.
- **Documentation**: Added `generate_docs.sh` to automate tool documentation using Gemini.
- **Testing**: Significant expansion of unit tests, especially for camera and rate-limiting logic.
- **Stability**: Added `intel-opencl-icd` check and better handling of hardware-specific optimizations.

---

## Version 0.4.0 (2026-03-04)

### New Features
- **Exchange Rates (`/rate`)**: Initial implementation to fetch current exchange rates for USD, EUR, and JPY against RUB.
    - Sourced from CBR.ru (via reliable JSON mirror) for stability.
    - Includes correct handling of currency nominals (e.g., JPY per 100 units).
    - Includes a signature link to `supopochi` Telegram channel.
- **Camera Video (`/camera video`)**: Implemented ability to record short video clips from ONVIF cameras.
    - Configurable duration (default 5s, max 30s).
    - Optimized for Telegram compatibility using `libx264` and `yuv420p`.
    - Note: Audio recording was removed to ensure compatibility and privacy.

### Improvements & Bug Fixes
- **FFmpeg Stability**: Improved RTSP stream handling by switching from `-stimeout` to `-timeout`.
- **Bot Protection Workarounds**: Successfully identified and handled bot protection on data sources by switching to more stable mirrors.
- **Improved Formatting**: Implemented global HTML parse mode and ensured all handlers use robust multi-line string formatting.
- **Testing**: Added unit tests for all new features (`/rate`, `/camera video`).
- **Project Guidelines**: Updated `GEMINI.md` with technical mandates for architecture, testing, and Git workflows to prevent common implementation errors.

---

## Version 0.3.0 (2026-03-03)

### New Features
- **Core Commands**: Implemented initial set of commands: `/time`, `/photo`, `/help`, and group management.
- **Logging System**: Added comprehensive command logging via middleware to capture all user interactions, including inline queries.
- **Admin Tools**:
    - **`/log` Command**: Display recent bot interactions with configurable line limits (`LOG_NUM_LINES`).
    - **`/top` Command**: Display most active users with configurable limits (`TOP_NUM_LINES`).
    - **Authorization**: Introduced `AdminMiddleware` and `.auth` file system to centralize authorization for restricted commands.
- **Weather Services**:
    - Enabled weather lookup via inline location sharing.
    - Expanded city list with a population script (`tools/populate_cities.py`).

### Improvements & Bug Fixes
- **Documentation**: Added detailed `README.md` covering features, requirements, setup, and usage.
- **Testing**: Added unit tests for `cmd_time` and `cmd_start` handlers.
- **Workflows**: Integrated Gemini GitHub Actions for automated dispatching, reviews, and triaging.
