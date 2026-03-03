import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database import update_user_status, update_user_location, get_user, get_sharing_users, get_user_by_username

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("share"))
async def cmd_share(message: types.Message, command: CommandObject):
    """Handles the /share [on|off|update|status] command."""
    args = command.args.strip().lower() if command.args else None
    user = message.from_user
    
    try:
        if args == "on":
            update_user_status(user.id, user.username, user.full_name, True)
            # Check if we already have a location
            user_record = get_user(user.id)
            if user_record and user_record['latitude'] is not None:
                await message.answer("Location sharing is now <b>ON</b>. I'll use your last known location. You can send a new location anytime to update it.")
            else:
                builder = ReplyKeyboardBuilder()
                builder.button(text="📍 Share Current Location", request_location=True)
                await message.answer(
                    "Location sharing is now <b>ON</b>! To start appearing in the circle, please share your current location using the button below:",
                    reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
                )
        elif args == "off":
            update_user_status(user.id, user.username, user.full_name, False)
            await message.answer("Location sharing is now <b>OFF</b>. You won't be visible on the map and won't see others.")
        elif args == "update":
            # Check if sharing is on
            user_record = get_user(user.id)
            if not user_record or not user_record['is_sharing']:
                await message.answer("Please turn on sharing first using <code>/share on</code>.")
                return
                
            builder = ReplyKeyboardBuilder()
            builder.button(text="📍 Update Location", request_location=True)
            await message.answer(
                "Please share your location to update your position in the circle:",
                reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
            )
        elif args == "status":
            user_record = get_user(user.id)
            if not user_record:
                status = "❌ Not sharing (no record)"
            elif user_record['is_sharing']:
                if user_record['latitude'] is not None:
                    status = f"✅ Sharing ON\n📍 Location: {user_record['latitude']}, {user_record['longitude']}\n⏰ Updated: {user_record['updated_at']}"
                else:
                    status = "✅ Sharing ON, but 📍 location not set yet. Send your location to start appearing on the map."
            else:
                status = "❌ Sharing is currently OFF."
            await message.answer(f"<b>Location Sharing Status:</b>\n\n{status}")
        else:
            await message.answer("Usage: <code>/share on</code>, <code>/share off</code>, <code>/share update</code>, or <code>/share status</code>")
    except Exception as e:
        logger.error(f"Error in cmd_share: {e}")
        await message.answer(f"Sorry, an error occurred while processing your request: {str(e)}")

@router.message(Command("map"))
async def cmd_map(message: types.Message, command: CommandObject):
    """Handles the /map [list|username] command."""
    # Mutual sharing check
    user_record = get_user(message.from_user.id)
    if not user_record or not user_record['is_sharing']:
        await message.answer("You must turn on location sharing (<code>/share on</code>) to see other users.")
        return

    args = command.args.strip().lower() if command.args else None
    if not args or args == "list":
        # List sharing users
        sharing_users = get_sharing_users()
        # Filter out users without coordinates
        sharing_users = [u for u in sharing_users if u['latitude'] is not None]
        
        if not sharing_users:
            await message.answer("No one is currently sharing their location in the circle. Make sure users have shared their location after turning sharing on.")
            return
            
        response = "<b>Circle of Friends:</b>\n\n"
        for u in sharing_users:
            name = u['username'] if u['username'] else u['full_name']
            response += f"• @{name} - <code>/map {name}</code>\n"
        
        await message.answer(response)
    else:
        # Show specific user location
        target_name = args
        target = get_user_by_username(target_name)
        
        if not target:
            await message.answer(f"Sorry, I couldn't find user @{target_name} in the system.")
            return
            
        if not target['is_sharing']:
            await message.answer(f"User @{target_name} is not sharing their location.")
            return

        if target['latitude'] is None:
            await message.answer(f"User @{target_name} has enabled sharing but hasn't provided their location yet.")
            return
            
        lat, lon = target['latitude'], target['longitude']
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        name = target['username'] if target['username'] else target['full_name']
        
        await message.answer(
            f"📍 <b>Location of @{name}:</b>\n"
            f"Updated: {target['updated_at']}\n\n"
            f"<a href='{maps_link}'>View on Google Maps</a>",
            disable_web_page_preview=False
        )

@router.message(F.location)
async def handle_circle_location_update(message: types.Message):
    """Automatically updates location for sharing users."""
    user = message.from_user
    user_record = get_user(user.id)
    
    # Only update if the user has opted in to sharing
    if user_record and user_record['is_sharing']:
        lat = message.location.latitude
        lon = message.location.longitude
        update_user_location(user.id, lat, lon)
        logger.info(f"Updated location for user {user.id} (@{user.username})")
        # Optional: notify the user only if they explicitly used /share update
        # For now, we remain silent as location might be shared for weather etc.
    
    # We do NOT return or stop propagation here, because other handlers (like weather) 
    # might still need to process this location message.
