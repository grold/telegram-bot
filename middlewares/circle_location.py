import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from database import get_user, update_user_location

logger = logging.getLogger(__name__)

class CircleLocationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Check if message contains a location
        if isinstance(event, Message) and event.location:
            user = event.from_user
            if user:
                user_record = get_user(user.id)
                # Only update if the user has opted in to sharing
                if user_record and user_record['is_sharing']:
                    lat = event.location.latitude
                    lon = event.location.longitude
                    update_user_location(user.id, lat, lon)
                    logger.info(f"Middleware updated location for user {user.id} (@{user.username})")

        return await handler(event, data)
