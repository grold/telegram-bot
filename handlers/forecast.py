import logging
import aiohttp
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import WEATHER_API_KEY

router = Router()
logger = logging.getLogger(__name__)

async def get_forecast(city_name: str = None, lat: float = None, lon: float = None):
    """Fetches 5-day/3-hour forecast from OpenWeatherMap."""
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

    url = "https://api.openweathermap.org/data/2.5/forecast"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    logger.error(f"OpenWeatherMap forecast returned status {response.status}: {error_data}")
                    return None
        except Exception as e:
            logger.exception(f"Error fetching forecast for {params.get('q') or (lat, lon)}")
            return None

def format_forecast_message(data: dict):
    """Formats the forecast data into a readable message."""
    try:
        city_name = data.get('city', {}).get('name', 'Unknown')
        country = data.get('city', {}).get('country', 'Unknown')
        
        # --- 3-Hour Forecast for the Next 24 Hours ---
        hourly_forecast_parts = ["<b>Next 24 Hours (3-hour intervals):</b>"]
        for forecast in data['list'][:8]:  # Next 8 intervals = 24 hours
            dt_object = datetime.fromtimestamp(forecast['dt'], tz=timezone.utc)
            local_time_str = dt_object.strftime('%H:%M')
            temp = forecast['main']['temp']
            condition = forecast['weather'][0]['main']
            hourly_forecast_parts.append(f"<code>{local_time_str}</code>: {temp}°C, <i>{condition}</i>")
        
        hourly_forecast_str = "\n".join(hourly_forecast_parts)

        # --- 5-Day Forecast Summary ---
        daily_summary = defaultdict(lambda: {'temps': [], 'conditions': defaultdict(int)})
        for forecast in data['list']:
            date_str = datetime.fromtimestamp(forecast['dt'], tz=timezone.utc).strftime('%Y-%m-%d')
            daily_summary[date_str]['temps'].append(forecast['main']['temp'])
            daily_summary[date_str]['conditions'][forecast['weather'][0]['main']] += 1

        daily_forecast_parts = ["\n<b>Next 5 Days:</b>"]
        for date, summary in sorted(daily_summary.items())[:5]:
            min_temp = min(summary['temps'])
            max_temp = max(summary['temps'])
            # Most common condition for the day
            main_condition = max(summary['conditions'], key=summary['conditions'].get)
            day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
            daily_forecast_parts.append(f"<code>{day_name}, {date}</code>: {min_temp:.1f}°C / {max_temp:.1f}°C, <i>{main_condition}</i>")
            
        daily_forecast_str = "\n".join(daily_forecast_parts)
        
        return (
            f"<b>🌤️ Forecast for {city_name}, {country}</b>\n\n"
            f"{hourly_forecast_str}\n"
            f"{daily_forecast_str}"
        )
    except Exception as e:
        logger.exception("Error formatting forecast message")
        return "Sorry, I couldn't format the forecast data correctly."

@router.message(Command("forecast"))
async def cmd_forecast(message: types.Message, command: CommandObject):
    """Handles the /forecast command."""
    city_query = command.args
    
    if city_query:
        data = await get_forecast(city_name=city_query)
        if data:
            await message.answer(format_forecast_message(data), parse_mode="HTML")
        else:
            await message.answer(f"Sorry, I couldn't find the forecast for: '{city_query}'.")
    else:
        builder = ReplyKeyboardBuilder()
        builder.button(text="📍 Share Location", request_location=True)
        await message.answer(
            "To show you the forecast for your location, please share it using the button below:",
            reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        )
