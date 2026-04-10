import pytest
import io
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image, ExifTags
from handlers.exif_weather import get_decimal_from_dms, extract_exif_data, get_weather_condition, fetch_historical_weather

def test_get_decimal_from_dms():
    # 52° 31' 12" N -> 52.52
    assert round(get_decimal_from_dms((52, 31, 12), 'N'), 2) == 52.52
    # 13° 24' 36" E -> 13.41
    assert round(get_decimal_from_dms((13, 24, 36), 'E'), 2) == 13.41
    # 33° 51' 31" S -> -33.8586...
    assert round(get_decimal_from_dms((33, 51, 31), 'S'), 4) == -33.8586

def test_get_decimal_from_dms_invalid_input():
    # Test invalid formats
    assert get_decimal_from_dms(None, 'N') is None
    assert get_decimal_from_dms((52, 31), 'N') is None
    assert get_decimal_from_dms("invalid", 'N') is None
    assert get_decimal_from_dms((52, 31, "invalid"), 'N') is None

def test_get_weather_condition():
    assert get_weather_condition(0) == "Clear sky"
    assert get_weather_condition(95) == "Thunderstorm"
    assert get_weather_condition(999) == "Unknown"

@patch('PIL.Image.open')
def test_extract_exif_data_success(mock_image_open):
    mock_img = MagicMock()
    mock_exif = MagicMock()
    mock_gps_ifd = {
        1: 'N', 2: (52, 0, 0),
        3: 'E', 4: (13, 0, 0),
    }
    # Mock exif.get for 0x9003 (DateTimeOriginal)
    mock_exif.get.side_effect = lambda key: "2023:05:20 12:00:00" if key == 0x9003 else None
    mock_exif.get_ifd.return_value = mock_gps_ifd
    mock_img.getexif.return_value = mock_exif
    mock_image_open.return_value = mock_img

    coords, dt_str = extract_exif_data(b"fake_image_bytes")
    assert coords == (52.0, 13.0)
    assert dt_str == "2023:05:20 12:00:00"

@patch('PIL.Image.open')
def test_extract_exif_data_no_exif(mock_image_open):
    mock_img = MagicMock()
    mock_img.getexif.return_value = None
    mock_image_open.return_value = mock_img

    coords, dt_str = extract_exif_data(b"fake_image_bytes")
    assert coords is None
    assert dt_str is None

@patch('PIL.Image.open')
def test_extract_exif_data_no_gps(mock_image_open):
    mock_img = MagicMock()
    mock_exif = MagicMock()
    mock_exif.get_ifd.return_value = None # No GPS IFD
    mock_img.getexif.return_value = mock_exif
    mock_image_open.return_value = mock_img

    coords, dt_str = extract_exif_data(b"fake_image_bytes")
    assert coords is None
    assert dt_str is None

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
