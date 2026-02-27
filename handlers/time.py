import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

router = Router()
geolocator = Nominatim(user_agent="telegram_bot_timezone_lookup")
tf = TimezoneFinder()
logger = logging.getLogger(__name__)

@router.message(Command("time"))
async def cmd_time(message: types.Message, command: CommandObject):
    """Shows the current time for a specified city or server local time by default."""
    city_query = command.args
    
    if not city_query:
        # Default to Server Local Time
        now = datetime.now().astimezone()
        tz_name = str(now.tzinfo) if now.tzinfo else "Local"
        display_name = "Server Local Time"
    else:
        try:
            # Geocode the city query
            location = geolocator.geocode(city_query)
            if not location:
                await message.answer(f"Sorry, I couldn't find the location: '{city_query}'.")
                return
            
            # Find the timezone name for those coordinates
            tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            if not tz_name:
                await message.answer(f"I found '{location.address}', but I couldn't determine its timezone.")
                return
            
            display_name = location.address.split(",")[0]  # Get the first part of the address
            now = datetime.now(ZoneInfo(tz_name))
            
        except Exception as e:
            logger.exception("Error during geocoding or timezone lookup")
            await message.answer("An error occurred while looking up the city. Please try again later.")
            return

    try:
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        
        await message.answer(
            f"The current time in <b>{display_name}</b> is:\n"
            f"🕒 <code>{time_str}</code>\n"
            f"📅 <code>{date_str}</code>\n"
            f"🌍 Timezone: <i>{tz_name}</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.exception(f"Error calculating time for timezone: {tz_name}")
        await message.answer("Error: Could not calculate the time for that location.")
