# VLC Link Generator (`get_vlc_link.py`)

This utility script connects to an ONVIF-compatible camera to retrieve its RTSP stream URI and formats it with embedded credentials for direct playback in VLC Media Player.

## Overview
The script automates the process of discovering the correct RTSP path for a camera's media profile. It handles ONVIF handshake, profile selection, and credential injection (`rtsp://user:pass@ip:port/path`) to ensure the generated link is ready for "copy-paste" use.

## Prerequisites
- **ONVIF Support**: The camera must support the ONVIF protocol.
- **Dependencies**: Requires `onvif-zeep` (imported as `onvif`).
- **Configuration**: Must have `CAMERA_IP`, `CAMERA_PORT`, `CAMERA_USER`, and `CAMERA_PASSWORD` defined in the project's `config.py` (typically loaded via `.env`).

## Usage
Run the script from the terminal:
```bash
python tools/get_vlc_link.py
```

### Output
The script will output a formatted block containing the network stream link:
```text
==================================================
VLC NETWORK STREAM LINK:
==================================================
rtsp://admin:password@192.168.1.100:554/live/ch1
==================================================
```

### How to use in VLC
1. Open **VLC Media Player**.
2. Go to **Media** -> **Open Network Stream** (or press `Ctrl+N`).
3. Paste the generated link into the URL field.
4. Click **Play**.

## Implementation Details
- **Media Profile**: By default, the script selects the first available media profile (`profiles[0]`), which is typically the highest resolution (Main Stream).
- **Credential Injection**: It automatically checks if the URI returned by the camera already contains credentials. If not, it injects them to prevent VLC from prompting for a login.
- **Error Handling**: Includes troubleshooting tips for common connection issues like incorrect IP, wrong ONVIF port, or invalid credentials.
