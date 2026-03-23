import logging
import asyncio
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from config import BOT_VERSION
from database import add_interaction_log

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
        
        # Get user role if it was set by AuthMiddleware
        user_role = data.get("user_role")
        
        # Log to SQLite (asynchronously to avoid blocking)
        asyncio.create_task(asyncio.to_thread(
            add_interaction_log,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            chat_id=chat.id if chat else None,
            chat_type=chat.type if chat else None,
            chat_title=getattr(chat, "title", None) if chat else None,
            message_id=message_id,
            content=content_desc,
            duration_ms=duration_ms,
            bot_version=BOT_VERSION,
            chat_username=getattr(chat, "username", None) if chat else None,
            user_role=user_role
        ))
        
        return result
