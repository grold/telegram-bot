import io
import logging
import aiohttp
from datetime import datetime
from PIL import Image, ExifTags
from aiogram import Router, types, F, Bot
from aiogram.types import FSInputFile

router = Router()
logger = logging.getLogger(__name__)

def get_decimal_from_dms(dms, ref):
    """Converts Degrees, Minutes, Seconds to decimal coordinates."""
    if not isinstance(dms, (list, tuple)) or len(dms) < 3:
        logger.warning(f"Invalid DMS format provided: {dms}")
        return None
    try:
        degrees = dms[0]
        minutes = dms[1]
        seconds = dms[2]
        
        # Pillow returns rational numbers which might be objects or tuples
        # Depending on the version, they could be floats or fractions
        d = float(degrees)
        m = float(minutes) / 60.0
        s = float(seconds) / 3600.0
        
        decimal = d + m + s
        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal
    except (TypeError, ValueError) as e:
        logger.exception(f"Error converting DMS to decimal: {e}")
        return None

def extract_exif_data(image_bytes):
    """Extracts GPS and Timestamp from image bytes."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif = img.getexif()
        if not exif:
            return None, None

        # Try to get GPS IFD specifically
        gps_ifd = exif.get_ifd(0x8825)
        if gps_ifd:
            # GPSLatitude is 2, GPSLatitudeRef is 1
            lat = get_decimal_from_dms(gps_ifd.get(2), gps_ifd.get(1))
            # GPSLongitude is 4, GPSLongitudeRef is 3
            lon = get_decimal_from_dms(gps_ifd.get(4), gps_ifd.get(3))
            
            # Timestamp
            dt_str = exif.get(0x9003) or exif.get(0x0132)
            if not dt_str:
                exif_ifd = exif.get_ifd(0x8769)
                if exif_ifd:
                    dt_str = exif_ifd.get(0x9003) or exif_ifd.get(0x9004)
            
            return (lat, lon), dt_str
        
        return None, None
    except (IOError, AttributeError, KeyError) as e:
        logger.exception(f"Error extracting EXIF data: {e}")
        return None, None

async def fetch_historical_weather(lat, lon, dt_str):
    """Fetches historical weather from Open-Meteo."""
    try:
        # EXIF date format: YYYY:MM:DD HH:MM:SS
        dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        date_str = dt.strftime("%Y-%m-%d")
        hour = dt.hour

        # Open-Meteo Archive API takes up to 2 days to update.
        # If the date is very recent, use the forecast API.
        days_diff = (datetime.now() - dt).days
        
        if days_diff <= 7:
            url = "https://api.open-meteo.com/v1/forecast"
        else:
            url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,cloud_cover",
            "timezone": "auto"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    hourly = data.get("hourly", {})
                    
                    # Safer data access
                    hourly_data_keys = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "cloud_cover", "weather_code"]
                    hourly_values = {key: hourly.get(key, []) for key in hourly_data_keys}

                    if all(len(hourly_values[key]) > hour for key in hourly_data_keys):
                        return {
                            "temp": hourly_values["temperature_2m"][hour],
                            "humidity": hourly_values["relative_humidity_2m"][hour],
                            "wind": hourly_values["wind_speed_10m"][hour],
                            "clouds": hourly_values["cloud_cover"][hour],
                            "code": hourly_values["weather_code"][hour],
                            "date": date_str,
                            "time": dt.strftime("%H:%M:%S")
                        }
                    else:
                        logger.error(f"Incomplete hourly data for hour {hour} in response.")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"Open-Meteo returned status {response.status}: {error_text}")
                    return None
    except (aiohttp.ClientError, KeyError, IndexError, ValueError) as e:
        logger.exception(f"Error fetching historical weather: {e}")
        return None

def get_weather_condition(code):
    """Maps Open-Meteo weather codes to readable descriptions."""
    # Simple mapping based on WMO Weather interpretation codes
    mapping = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    return mapping.get(code, "Unknown")

async def process_photo_for_exif(message: types.Message, bot: Bot, file_id: str):
    """Common logic for processing photo or document."""
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    # Convert BytesIO to raw bytes
    raw_bytes = file_bytes.read()
    
    coords, dt_str = extract_exif_data(raw_bytes)
    
    if coords and coords[0] is not None and coords[1] is not None and dt_str:
        lat, lon = coords
        weather = await fetch_historical_weather(lat, lon, dt_str)
        
        if weather:
            condition = get_weather_condition(weather['code'])
            
            # Send map
            await message.answer_location(latitude=lat, longitude=lon)
            
            # Send report
            report = (
                f"<b>📍 Photo Location:</b> <code>{lat:.4f}, {lon:.4f}</code>\n"
                f"<b>📅 Taken on:</b> <code>{weather['date']}</code> at <code>{weather['time']}</code>\n\n"
                f"🌡️ <b>Temperature:</b> <code>{weather['temp']}°C</code>\n"
                f"☁️ <b>Condition:</b> <code>{condition}</code>\n"
                f"💧 <b>Humidity:</b> <code>{weather['humidity']}%</code>\n"
                f"💨 <b>Wind Speed:</b> <code>{weather['wind']} km/h</code>\n"
                f"🌥️ <b>Cloud Cover:</b> <code>{weather['clouds']}%</code>"
            )
            await message.answer(report)
        else:
            logger.info(f"Could not fetch weather for coordinates {coords} and date {dt_str}")
    else:
        logger.info(f"No EXIF GPS/Date found in file {file_id} from user {message.from_user.id}")

@router.message(F.photo)
async def handle_photo(message: types.Message, bot: Bot):
    # Get the highest resolution photo
    photo = message.photo[-1]
    await process_photo_for_exif(message, bot, photo.file_id)

@router.message(F.document)
async def handle_document(message: types.Message, bot: Bot):
    if message.document.mime_type and message.document.mime_type.startswith("image/"):
        await process_photo_for_exif(message, bot, message.document.file_id)
