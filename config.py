import os
import tomllib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_version():
    try:
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "unknown")
    except Exception:
        return "unknown"

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TOP_NUM_LINES = int(os.getenv("TOP_NUM_LINES", "10"))
LOG_NUM_LINES = int(os.getenv("LOG_NUM_LINES", "10"))
BOT_VERSION = get_version()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file")
