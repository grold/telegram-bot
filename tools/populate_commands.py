import logging
import asyncio
from database import init_db, update_command_details
from config import BOT_VERSION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_COMMANDS = [
    ("start", "PUBLIC", "Welcome message and bot introduction"),
    ("help", "PUBLIC", "Show available commands and usage guide"),
    ("weather", "PUBLIC", "Get current weather for a city or location"),
    ("forecast", "PUBLIC", "Get 5-day weather forecast"),
    ("time", "PUBLIC", "Check local time in any city"),
    ("rate", "PUBLIC", "Check currency exchange rates"),
    ("webcams", "PUBLIC", "Interact with Windy webcams"),
    ("share", "USER", "Manage your location sharing status"),
    ("map", "USER", "View mutual friends on an interactive map"),
    ("camera", "USER", "Capture snapshots or video from bot camera"),
    ("photo", "ADMIN", "Receive a random curated photo"),
    ("top", "ADMIN", "View server resource usage statistics"),
    ("log", "ADMIN", "View recent bot activity logs"),
    ("mygroups", "ADMIN", "List groups where the bot is present"),
    ("grant", "OWNER", "Grant authorization and roles to users"),
    ("revoke", "OWNER", "Revoke user authorization"),
    ("list_authorized", "ADMIN", "Show active authorized users"),
    ("set_access", "OWNER", "Configure command permission levels"),
]

async def populate_commands():
    """Seeds the database with the initial set of commands."""
    logger.info(f"Populating commands for bot version {BOT_VERSION}...")
    init_db()
    
    for cmd, role, desc in INITIAL_COMMANDS:
        update_command_details(cmd, min_role=role, description=desc, is_visible=True)
        logger.info(f"Added/Updated command: /{cmd} ({role}) - {desc}")
    
    logger.info("Command population complete.")

if __name__ == "__main__":
    asyncio.run(populate_commands())
