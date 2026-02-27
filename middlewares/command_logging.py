import logging
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from config import BOT_VERSION

# Setup a dedicated logger for interactions
COMMAND_LOG_FILE = "commands.log"
interaction_logger = logging.getLogger("interaction_log")
interaction_logger.setLevel(logging.INFO)

# Create a file handler if it doesn't exist
if not interaction_logger.handlers:
    fh = logging.FileHandler(COMMAND_LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    interaction_logger.addHandler(fh)

class InteractionLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        start_time = time.perf_counter()
        
        # Determine the user
        user = getattr(event, "from_user", None)
        if not user:
            return await handler(event, data)
            
        # Optional chat info
        chat = getattr(event, "chat", None)
        
        user_info = f"ID: {user.id}, @{user.username or 'N/A'}, Name: {user.full_name}, Lang: {user.language_code or 'N/A'}"
        
        chat_info = ""
        if chat:
            chat_info = f"Chat [ID: {chat.id}, Type: {chat.type}"
            if getattr(chat, "title", None):
                chat_info += f", Title: {chat.title}"
            chat_info += "] "
            
        message_id_info = ""
        message_id = getattr(event, "message_id", None)
        if message_id:
            message_id_info = f"[MsgID: {message_id}] "
            
        # Find the text or query content
        if getattr(event, "text", None):
            content_desc = event.text
        elif getattr(event, "query", None) is not None:  # In case the query is empty string
            content_desc = f"[InlineQuery] {event.query}"
        elif getattr(event, "caption", None):
            content_desc = f"[Media] {event.caption}"
        else:
            content_desc = f"[{type(event).__name__}]"

        # Execute the handler
        result = await handler(event, data)
        
        # Post-execution calculation
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Final log entry
        log_entry = (
            f"[v{BOT_VERSION}] {chat_info}{message_id_info}"
            f"User [{user_info}] interacted: {content_desc} "
            f"[Duration: {duration_ms:.2f}ms]"
        )
        interaction_logger.info(log_entry)
        
        return result
