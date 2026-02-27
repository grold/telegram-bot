import logging
import aiohttp
from datetime import datetime, timezone, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import WEATHER_API_KEY

router = Router()
logger = logging.getLogger(__name__)

async def get_weather(city_name: str = None, lat: float = None, lon: float = None):
    """Fetches weather from OpenWeatherMap using city name or coordinates."""
    if not WEATHER_API_KEY:
        logger.error("WEATHER_API_KEY is not set.")
        return None

    params = {'appid': WEATHER_API_KEY, 'units': 'metric'}
    if city_name:
        params['q'] = city_name
    elif lat is not None and lon is not None:
        params['lat'] = lat
        params['lon'] = lon
    else:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    logger.error(f"OpenWeatherMap returned status {response.status}: {error_data}")
                    return None
        except Exception as e:
            logger.exception(f"Error fetching weather for {params.get('q') or (lat, lon)}")
            return None

def format_weather_message(data: dict):
    """Formats the OpenWeatherMap data into a detailed, readable message."""
    try:
        # Core data
        weather_list = data.get("weather", [{}])
        condition = weather_list[0].get("description", "Unknown").capitalize()
        main = data.get("main", {})
        temp = main.get("temp")
        feels_like = main.get("feels_like")
        humidity = main.get("humidity")
        pressure = main.get("pressure")
        city = data.get("name", "Unknown")
        country = data.get("sys", {}).get("country", "Unknown")
        
        # Wind
        wind_speed_ms = data.get("wind", {}).get("speed", 0)
        wind_speed_kmh = round(wind_speed_ms * 3.6, 1)

        # Visibility
        visibility_meters = data.get("visibility", 0)
        visibility_km = round(visibility_meters / 1000, 1)

        # Cloudiness
        cloudiness = data.get("clouds", {}).get("all", "N/A")

        # Sunrise & Sunset
        timezone_offset = data.get("timezone", 0)
        tz = timezone(timedelta(seconds=timezone_offset))
        sunrise_ts = data.get("sys", {}).get("sunrise", 0)
        sunset_ts = data.get("sys", {}).get("sunset", 0)
        sunrise_time = datetime.fromtimestamp(sunrise_ts, tz=tz).strftime('%H:%M:%S')
        sunset_time = datetime.fromtimestamp(sunset_ts, tz=tz).strftime('%H:%M:%S')
        
        return (
            f"<b>📍 Weather in {city}, {country}</b>\n\n"
            f"🌡️ <b>Temperature:</b> <code>{temp}°C</code>\n"
            f"🤔 <b>Feels Like:</b> <code>{feels_like}°C</code>\n"
            f"☁️ <b>Condition:</b> <code>{condition}</code>\n"
            f"💧 <b>Humidity:</b> <code>{humidity}%</code>\n"
            f"💨 <b>Wind:</b> <code>{wind_speed_kmh} km/h</code>\n"
            f"👀 <b>Visibility:</b> <code>{visibility_km} km</code>\n"
            f"📊 <b>Pressure:</b> <code>{pressure} hPa</code>\n"
            f"🌥️ <b>Cloudiness:</b> <code>{cloudiness}%</code>\n\n"
            f"🌅 <b>Sunrise:</b> <code>{sunrise_time}</code>\n"
            f"🌇 <b>Sunset:</b> <code>{sunset_time}</code>"
        )
    except Exception as e:
        logger.exception("Error formatting weather message")
        return "Sorry, I couldn't format the weather data correctly."

@router.message(Command("weather"))
async def cmd_weather(message: types.Message, command: CommandObject):
    """Handles the /weather command."""
    city_query = command.args
    
    if city_query:
        # Fetch weather for the provided city
        data = await get_weather(city_name=city_query)
        if data:
            await message.answer(format_weather_message(data), parse_mode="HTML")
        else:
            await message.answer(f"Sorry, I couldn't find the weather for: '{city_query}'.")
    else:
        # Prompt for location
        builder = ReplyKeyboardBuilder()
        builder.button(text="📍 Share Location", request_location=True)
        
        await message.answer(
            "To show you the weather for your current location, please click the button below:",
            reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )

@router.message(F.location)
async def handle_location(message: types.Message):
    """Handles shared location to provide both weather and forecast."""
    lat = message.location.latitude
    lon = message.location.longitude
    
    # Get weather data
    weather_data = await get_weather(lat=lat, lon=lon)
    if weather_data:
        await message.answer(
            format_weather_message(weather_data),
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Sorry, I couldn't fetch the current weather for your location.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return  # Stop if weather fails

    # Get forecast data
    # We can reuse the other file's functions by importing them
    from handlers.forecast import get_forecast, format_forecast_message
    forecast_data = await get_forecast(lat=lat, lon=lon)
    if forecast_data:
        await message.answer(
            format_forecast_message(forecast_data),
            parse_mode="HTML"
        )
    else:
        await message.answer("Could not fetch the forecast for your location.")
