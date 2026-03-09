import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Union
from pathlib import Path

# Configure logging to stdout for CLI
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("cli_mock")

@dataclass
class MockUser:
    id: int = 123456789
    is_bot: bool = False
    first_name: str = "CLI"
    last_name: str = "User"
    username: str = "cli_user"
    language_code: str = "en"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

@dataclass
class MockChat:
    id: int = 987654321
    type: str = "private"
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class MockBot:
    def __init__(self, token: str = "mock_token"):
        self.token = token
    
    async def get_me(self):
        return MockUser(id=999, is_bot=True, first_name="MockBot", username="mock_bot")
        
    async def get_file(self, file_id: str):
        # Return a mock file object if needed
        pass
        
    async def download_file(self, file_path: str, destination: Union[str, Path]):
        # Mock download - maybe copy if it's a local path?
        logger.info(f"[MockBot] Downloading {file_path} to {destination}")

@dataclass
class MockMessage:
    message_id: int = 1
    date: int = 0
    chat: MockChat = field(default_factory=MockChat)
    from_user: MockUser = field(default_factory=MockUser)
    text: Optional[str] = None
    bot: MockBot = field(default_factory=MockBot)
    voice: Any = None
    audio: Any = None
    location: Any = None
    
    async def answer(self, text: str, parse_mode: str = None, reply_markup: Any = None, disable_web_page_preview: bool = False):
        print("\n--- [BOT ANSWER] ---")
        print(text)
        print("--------------------\n")
        return self

    async def reply(self, text: str, parse_mode: str = None, reply_markup: Any = None):
        print("\n--- [BOT REPLY] ---")
        print(text)
        print("-------------------\n")
        return self
        
    async def answer_photo(self, photo: Any, caption: str = None, **kwargs):
        print("\n--- [BOT SEND PHOTO] ---")
        print(f"Photo: {photo}")
        if caption:
            print(f"Caption: {caption}")
        print("------------------------\n")
        
    async def answer_video(self, video: Any, caption: str = None, **kwargs):
        print("\n--- [BOT SEND VIDEO] ---")
        print(f"Video: {video}")
        if caption:
            print(f"Caption: {caption}")
        print("------------------------\n")

    async def answer_location(self, latitude: float, longitude: float, **kwargs):
        print("\n--- [BOT SEND LOCATION] ---")
        print(f"Lat: {latitude}, Lon: {longitude}")
        print(f"Maps: https://www.google.com/maps?q={latitude},{longitude}")
        print("---------------------------\n")
        
    async def delete(self):
        print("[MockMessage] Message deleted.")

@dataclass
class MockCommandObject:
    prefix: str = "/"
    command: str = "command"
    mention: Optional[str] = None
    args: Optional[str] = None
