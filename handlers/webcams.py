import logging
import aiohttp
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import WINDY_API_KEY
from handlers.weather import get_weather

router = Router()
logger = logging.getLogger(__name__)

WINDY_API_URL = "https://api.windy.com/webcams/api/v3"
DEFAULT_WEBCAM_RADIUS_KM = 30


class WindyAPIError(Exception):
    """Base exception for Windy API errors."""
    pass


async def _fetch_windy(endpoint: str, params: dict = None):
    """Helper to fetch data from Windy API."""
    if not WINDY_API_KEY:
        raise WindyAPIError("WINDY_API_KEY is not set in _fetch_windy.")

    headers = {"x-windy-api-key": WINDY_API_KEY}
    url = f"{WINDY_API_URL}{endpoint}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Windy API error {response.status} for {url}: {await response.text()}")
                    return None
        except Exception:
            logger.exception(f"Exception fetching Windy API URL: {url}")
            return None


def _parse_list_or_dict(data, key):
    """Helper to parse list of items or dict with specific key."""
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and key in data:
        return data[key]
    return []


async def get_webcams_list(nearby=None, country=None, category=None, limit=10, offset=0):
    """Fetches a list of webcams based on filters."""
    params = {"limit": limit, "offset": offset, "include": "images,location,categories"}
    if nearby:
        params["nearby"] = nearby
    if country:
        params["country"] = country
    if category:
        params["category"] = category

    return await _fetch_windy("/webcams", params)


async def get_webcam_details(webcam_id: str):
    """Fetches details for a specific webcam."""
    return await _fetch_windy(f"/webcams/{webcam_id}", params={"include": "images,location,categories,player"})


async def get_categories():
    """Fetches available categories."""
    return await _fetch_windy("/categories")


async def get_countries():
    """Fetches available countries."""
    return await _fetch_windy("/countries")


async def get_regions(country_code: str = None):
    """Fetches available regions."""
    params = {}
    if country_code:
        params["country"] = country_code
    return await _fetch_windy("/regions", params)


async def get_continents():
    """Fetches available continents."""
    return await _fetch_windy("/continents")


async def _handle_webcams_city(message: types.Message, subcommand: str, args: list):
    """Handles 'city' and 'cities' subcommands."""
    if len(args) < 2:
        await message.answer(f"Please provide a city name: <code>/webcams {subcommand} London</code>")
        return

    city_query = " ".join(args[1:])
    msg = await message.answer(f"🔍 Searching for webcams in {city_query}...")

    try:
        weather_data = await get_weather(city_name=city_query)
        if not weather_data:
            await msg.edit_text(f"❌ Could not find location: {city_query}")
            return

        lat = weather_data.get("coord", {}).get("lat")
        lon = weather_data.get("coord", {}).get("lon")

        limit = 1 if subcommand == "city" else 10
        webcams_data = await get_webcams_list(
            nearby=f"{lat},{lon},{DEFAULT_WEBCAM_RADIUS_KM}",
            limit=limit
        )

        if webcams_data and webcams_data.get("webcams"):
            if subcommand == "city":
                cam = webcams_data["webcams"][0]
                title = cam.get("title", "Unknown Webcam")
                images = cam.get("images", {}).get("current", {})
                preview_url = images.get("preview") or images.get("thumbnail") or images.get("icon")

                city_name = cam.get("location", {}).get("city", city_query)
                country = cam.get("location", {}).get("country", "")

                caption = (
                    f"<b>📸 {title}</b>\n"
                    f"📍 {city_name}, {country}\n"
                    f"🆔 <code>{cam['webcamId']}</code>"
                )

                if preview_url:
                    await message.answer_photo(preview_url, caption=caption)
                    await msg.delete()
                else:
                    await msg.edit_text(f"📷 Found webcam '{title}' but no image is available.")
            else:
                text = f"<b>📸 Webcams in {city_query}</b>\n\n"
                for cam in webcams_data["webcams"]:
                    title = cam.get("title", "Untitled")
                    cam_id = cam.get("webcamId")
                    text += f"📷 <b>{title}</b>\n🆔 <code>{cam_id}</code>\n/webcams id {cam_id}\n\n"
                await msg.edit_text(text)
        else:
            await msg.edit_text(f"❌ No webcams found near {city_query}.")
    except WindyAPIError as e:
        logger.error(f"Windy API Error: {e}")
        await msg.edit_text("❌ Webcam service is currently unavailable.")
    except Exception:
        logger.exception("Error handling webcams city command")
        await msg.edit_text("❌ An error occurred while searching for webcams.")


async def _handle_webcams_list(message: types.Message, subcommand: str, args: list):
    """Handles 'list', 'country', and 'category' subcommands."""
    kwargs = {"limit": 5}
    title_prefix = "Webcams"

    if subcommand == "country":
        if len(args) < 2:
            await message.answer("Usage: <code>/webcams country [code]</code> (e.g., US, FR)")
            return
        code = args[1].upper()
        kwargs["country"] = code
        title_prefix = f"Webcams in {code}"

    elif subcommand == "category":
        if len(args) < 2:
            await message.answer("Usage: <code>/webcams category [name]</code> (e.g., beach, city)")
            return
        cat = args[1].lower()
        kwargs["category"] = cat
        title_prefix = f"Category: {cat}"

    try:
        data = await get_webcams_list(**kwargs)
        if data and data.get("webcams"):
            text = f"<b>{title_prefix}</b>\n\n"
            for cam in data["webcams"]:
                title = cam.get("title", "Untitled")
                cam_id = cam.get("webcamId")
                loc = cam.get("location", {})
                city = loc.get("city", "Unknown City")
                country = loc.get("country", "")
                text += f"📷 <b>{title}</b> ({city}, {country})\n🆔 <code>/webcams id {cam_id}</code>\n\n"
            await message.answer(text)
        else:
            await message.answer(f"No webcams found for {subcommand}.")
    except WindyAPIError as e:
        logger.error(f"Windy API Error: {e}")
        await message.answer("❌ Webcam service is currently unavailable.")
    except Exception:
        logger.exception("Error handling webcams list command")
        await message.answer("❌ An error occurred while fetching webcams.")


async def _handle_webcams_id(message: types.Message, args: list):
    """Handles 'id' subcommand."""
    if len(args) < 2:
        await message.answer("Usage: <code>/webcams id [ID]</code>")
        return

    cam_id = args[1]
    try:
        data = await get_webcam_details(cam_id)
        if not data:
            await message.answer("Failed to fetch webcam details.")
            return

        cam = data.get("webcam") or (data["webcams"][0] if data.get("webcams") else None)
        if not cam and "webcamId" in data:
            cam = data

        if cam:
            title = cam.get("title", "Unknown")
            images = cam.get("images", {}).get("current", {})
            preview_url = images.get("preview") or images.get("thumbnail") or images.get("icon")

            player = cam.get("player", {})

            def get_player_link(p_dict, key):
                val = p_dict.get(key, "")
                if isinstance(val, dict):
                    return val.get("embed", "")
                return val if isinstance(val, str) else ""

            day_link = get_player_link(player, "day")
            live_link = get_player_link(player, "live")
            player_link = live_link or day_link or ""

            caption = (
                f"<b>📷 {title}</b>\n"
                f"🆔 <code>{cam.get('webcamId')}</code>\n"
                f"📍 {cam.get('location', {}).get('city')}, {cam.get('location', {}).get('country')}\n"
                f"📅 Status: {cam.get('status')}\n"
            )
            if player_link:
                caption += f"▶️ <a href='{player_link}'>Watch Live/Timelapse</a>"

            if preview_url:
                await message.answer_photo(preview_url, caption=caption)
            else:
                await message.answer(caption)
        else:
            await message.answer("Webcam details not found.")
    except WindyAPIError as e:
        logger.error(f"Windy API Error: {e}")
        await message.answer("❌ Webcam service is currently unavailable.")
    except Exception:
        logger.exception("Error handling webcams id command")
        await message.answer("❌ An error occurred while fetching webcam details.")


async def _handle_metadata(message: types.Message, subcommand: str, args: list):
    """Handles metadata subcommands: categories, countries, regions, continents."""
    try:
        if subcommand == "categories":
            data = await get_categories()
            items = _parse_list_or_dict(data, "categories")
            if items:
                cats = [c.get("id") for c in items if isinstance(c, dict)]
                await message.answer(f"<b>Available Categories:</b>\n{', '.join(cats)}")
            else:
                await message.answer("No categories found or an unexpected format was received.")

        elif subcommand == "countries":
            data = await get_countries()
            items = _parse_list_or_dict(data, "countries")
            if items:
                countries = [c.get("id", c.get("code")) for c in items if isinstance(c, dict)]
                shown = countries[:50]
                text = f"<b>Countries ({len(countries)}):</b>\n{', '.join(shown)}"
                if len(countries) > 50:
                    text += "..."
                await message.answer(text)
            else:
                await message.answer("No countries found or an unexpected format was received.")

        elif subcommand == "regions":
            country_code = args[1] if len(args) > 1 else None
            data = await get_regions(country_code)
            items = _parse_list_or_dict(data, "regions")
            if items:
                regions = [r.get("id", r.get("name")) for r in items if isinstance(r, dict)]
                shown = regions[:50]
                text = f"<b>Regions:</b>\n{', '.join(shown)}"
                if len(regions) > 50:
                    text += "..."
                await message.answer(text)
            else:
                await message.answer("No regions found or an unexpected format was received.")

        elif subcommand == "continents":
            data = await get_continents()
            items = _parse_list_or_dict(data, "continents")
            if items:
                continents = [c.get("id", c.get("name")) for c in items if isinstance(c, dict)]
                await message.answer(f"<b>Continents:</b>\n{', '.join(continents)}")
            else:
                await message.answer("No continents found or an unexpected format was received.")
    except WindyAPIError as e:
        logger.error(f"Windy API Error: {e}")
        await message.answer("❌ Webcam service is currently unavailable.")
    except Exception:
        logger.exception(f"Error handling webcams metadata command: {subcommand}")
        await message.answer("❌ An error occurred while fetching metadata.")


@router.message(Command("webcams"))
async def cmd_webcams(message: types.Message, command: CommandObject):
    """Handles /webcams command with subcommands."""
    args = command.args.split() if command.args else []

    if not args:
        lines = [
            "<b>📸 Windy Webcams Commands:</b>",
            "• <code>/webcams city [name]</code> - Get a live webcam image for a city.",
            "• <code>/webcams cities [name]</code> - List webcam IDs available in a city.",
            "• <code>/webcams nearby</code> - Get webcams near your location.",
            "• <code>/webcams country [code]</code> - List webcams in a country (e.g., US, DE).",
            "• <code>/webcams category [cat]</code> - List webcams in a category.",
            "• <code>/webcams id [ID]</code> - Get details for a specific webcam.",
            "• <code>/webcams list</code> - List popular webcams.",
            "• <code>/webcams categories</code> - List available categories.",
            "• <code>/webcams countries</code> - List available countries.",
            "• <code>/webcams regions [country]</code> - List regions.",
            "• <code>/webcams continents</code> - List continents."
        ]
        await message.answer("\n".join(lines))
        return

    subcommand = args[0].lower()

    if subcommand in ["city", "cities"]:
        await _handle_webcams_city(message, subcommand, args)
    elif subcommand == "nearby":
        builder = InlineKeyboardBuilder()
        builder.button(text="📍 Share Location", callback_data="webcams_nearby_trigger")
        await message.answer("Click to find webcams near you:", reply_markup=builder.as_markup())
    elif subcommand in ["list", "country", "category"]:
        await _handle_webcams_list(message, subcommand, args)
    elif subcommand == "id":
        await _handle_webcams_id(message, args)
    elif subcommand in ["categories", "countries", "regions", "continents"]:
        await _handle_metadata(message, subcommand, args)
    else:
        await message.answer("Unknown subcommand. Try <code>/webcams</code> for help.")


@router.callback_query(F.data == "webcams_nearby_trigger")
async def webcams_nearby_trigger(callback: types.CallbackQuery):
    """Trigger asking for location."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📍 Share Location", request_location=True)
    await callback.message.answer(
        "Please share your location to find nearby webcams:",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await callback.answer()
