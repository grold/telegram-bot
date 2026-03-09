import os
import tomllib
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_git_branch():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None

def get_version():
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            version = data.get("project", {}).get("version", "unknown")
            branch = get_git_branch()
            if branch and branch != "HEAD":
                return f"{version}-{branch}"
            return version
    except Exception:
        return "unknown"

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WINDY_API_KEY = os.getenv("WINDY_API_KEY")
TOP_NUM_LINES = int(os.getenv("TOP_NUM_LINES", "10"))
LOG_NUM_LINES = int(os.getenv("LOG_NUM_LINES", "10"))
AUDIO_FOLDER = Path(os.getenv("AUDIO_FOLDER", "audio"))
AUDIO_CLEANUP_DAYS = int(os.getenv("AUDIO_CLEANUP_DAYS", "30"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "map.db")
SCREENSHOTS_DIR = Path(os.getenv("SCREENSHOTS_DIR", "screenshots"))
CAMERA_IP = os.getenv("CAMERA_IP", "10.1.100.151")
CAMERA_PORT = int(os.getenv("CAMERA_PORT", "8000"))
CAMERA_USER = os.getenv("CAMERA_USER", "onvif_login")
CAMERA_PASSWORD = os.getenv("CAMERA_PASSWORD", "onvif_password")
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", "30"))
FONT_PATH = os.getenv("FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
BOT_VERSION = get_version()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file")
