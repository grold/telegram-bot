# Version 0.4.0

## Changes since v0.3.0

### New Features
- **Exchange Rates (`/rate`)**: Added a new command to fetch current exchange rates for USD, EUR, and JPY against RUB.
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
