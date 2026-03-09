# Version 0.5.0

## Changes since v0.4.0

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

### Technical Updates
- Updated `GEMINI.md` with new technical mandates for Whisper acceleration, image processing, and consistent `parse_mode`.
- Incremented version to `0.5.0`.
