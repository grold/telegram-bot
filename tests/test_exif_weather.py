import pytest
import io
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image, ImageOps
from handlers.exif_weather import get_decimal_from_dms, extract_exif_data, get_weather_condition, fetch_historical_weather

def create_test_image_with_exif(lat=None, lon=None, date_str=None):
    """Creates a small image with EXIF metadata for testing."""
    img = Image.new('RGB', (10, 10), color='red')
    exif = img.getexif()
    
    if lat is not None and lon is not None:
        # GPS IFD is 0x8825
        gps_ifd = {
            1: 'N' if lat >= 0 else 'S',
            2: (abs(lat), 0, 0), # Simplified DMS
            3: 'E' if lon >= 0 else 'W',
            4: (abs(lon), 0, 0),
        }
        # In real EXIF, these are rationals (num, den). Pillow handles some tuples.
        # This is a simplified mock for extract_exif_data to process.
        
    # DateTimeOriginal is 0x9003
    if date_str:
        exif[0x9003] = date_str
        
    img_byte_arr = io.BytesIO()
    # img.save(img_byte_arr, format='JPEG', exif=exif) # Pillow might not save all IFDs easily this way in tests
    # return img_byte_arr.getvalue()
    return img, exif

def test_get_decimal_from_dms():
    # 52° 31' 12" N -> 52.52
    assert round(get_decimal_from_dms((52, 31, 12), 'N'), 2) == 52.52
    # 13° 24' 36" E -> 13.41
    assert round(get_decimal_from_dms((13, 24, 36), 'E'), 2) == 13.41
    # 33° 51' 31" S -> -33.8586...
    assert round(get_decimal_from_dms((33, 51, 31), 'S'), 4) == -33.8586

def test_get_weather_condition():
    assert get_weather_condition(0) == "Clear sky"
    assert get_weather_condition(95) == "Thunderstorm"
    assert get_weather_condition(999) == "Unknown"

@pytest.mark.asyncio
async def test_fetch_historical_weather_success():
    mock_response = {
        "hourly": {
            "temperature_2m": [10.0] * 24,
            "relative_humidity_2m": [50] * 24,
            "wind_speed_10m": [5.0] * 24,
            "cloud_cover": [10] * 24,
            "weather_code": [0] * 24
        }
    }
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_ctx = MagicMock()
        mock_ctx.__aenter__.return_value.status = 200
        mock_ctx.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        mock_get.return_value = mock_ctx
        
        result = await fetch_historical_weather(52.52, 13.41, "2023:05:20 12:00:00")
        
        assert result is not None
        assert result['temp'] == 10.0
        assert result['date'] == "2023-05-20"
        assert result['time'] == "12:00:00"

@patch('handlers.exif_weather.extract_exif_data')
@patch('handlers.exif_weather.fetch_historical_weather')
@pytest.mark.asyncio
async def test_handle_photo_success(mock_fetch, mock_extract):
    # Mock data
    mock_extract.return_value = ((52.52, 13.41), "2023:05:20 12:00:00")
    mock_fetch.return_value = {
        "temp": 20.5, "humidity": 45, "wind": 12, "clouds": 5, "code": 0,
        "date": "2023-05-20", "time": "12:00:00"
    }
    
    # Mock message and bot
    message = AsyncMock()
    bot = AsyncMock()
    photo = MagicMock()
    photo.file_id = "test_file_id"
    message.photo = [photo]
    
    # Mock bot methods
    file_mock = MagicMock()
    file_mock.file_path = "path/to/file"
    bot.get_file.return_value = file_mock
    
    # Mock download_file
    download_mock = MagicMock()
    download_mock.read.return_value = b"fake_bytes"
    bot.download_file.return_value = download_mock
    
    from handlers.exif_weather import handle_photo
    await handle_photo(message, bot)
    
    # Verify outcomes
    message.answer_location.assert_called_once_with(latitude=52.52, longitude=13.41)
    message.answer.assert_called_once()
    assert "20.5°C" in message.answer.call_args[0][0]

@patch('handlers.exif_weather.extract_exif_data')
@pytest.mark.asyncio
async def test_handle_photo_no_exif(mock_extract):
    mock_extract.return_value = (None, None)
    
    message = AsyncMock()
    bot = AsyncMock()
    photo = MagicMock()
    message.photo = [photo]
    bot.get_file.return_value = MagicMock(file_path="path")
    bot.download_file.return_value = MagicMock(read=lambda: b"bytes")
    
    from handlers.exif_weather import handle_photo
    await handle_photo(message, bot)
    
    # Should NOT reply to user
    message.answer_location.assert_not_called()
    message.answer.assert_not_called()
