import logging
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from config import BOT_VERSION

# Setup a dedicated logger for commands
COMMAND_LOG_FILE = "commands.log"
command_logger = logging.getLogger("command_execution")
command_logger.setLevel(logging.INFO)

# Create a file handler if it doesn't exist
if not command_logger.handlers:
    fh = logging.FileHandler(COMMAND_LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    command_logger.addHandler(fh)

class CommandLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Only log if it's a command
        is_command = event.text and event.text.startswith("/")
        
        if not is_command:
            return await handler(event, data)

        start_time = time.perf_counter()
        
        # Pre-execution data collection
        user = event.from_user
        chat = event.chat
        
        user_info = f"ID: {user.id}, @{user.username or 'N/A'}, Name: {user.full_name}, Lang: {user.language_code or 'N/A'}"
        chat_info = f"ID: {chat.id}, Type: {chat.type}"
        if chat.title:
            chat_info += f", Title: {chat.title}"
            
        message_id = event.message_id
        command_text = event.text.split()[0] # Log only the command itself to keep it clean, or keep full text? 
                                            # Let's keep full text but identify the command.

        # Execute the handler
        result = await handler(event, data)
        
        # Post-execution calculation
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Final log entry
        log_entry = (
            f"[v{BOT_VERSION}] [{chat_info}] [MsgID: {message_id}] "
            f"User [{user_info}] executed: {event.text} "
            f"[Duration: {duration_ms:.2f}ms]"
        )
        command_logger.info(log_entry)
        
        return result
