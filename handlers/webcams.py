import logging
import aiohttp
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import WINDY_API_KEY
from handlers.weather import get_weather

router = Router()
logger = logging.getLogger(__name__)

WINDY_API_URL = "https://api.windy.com/webcams/api/v3"

async def _fetch_windy(endpoint: str, params: dict = None):
    """Helper to fetch data from Windy API."""
    if not WINDY_API_KEY:
        logger.error("WINDY_API_KEY is not set.")
        return None
    
    headers = {"x-windy-api-key": WINDY_API_KEY}
    url = f"{WINDY_API_URL}{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Windy API error {response.status}: {await response.text()}")
                    return None
        except Exception as e:
            logger.exception(f"Exception fetching Windy API: {e}")
            return None

async def get_webcams_list(nearby=None, country=None, category=None, limit=10, offset=0):
    """Fetches a list of webcams based on filters."""
    params = {"limit": limit, "offset": offset, "include": "images,location,categories"}
    if nearby:
        params["nearby"] = nearby # lat,lon,radius
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

@router.message(Command("webcams"))
async def cmd_webcams(message: types.Message, command: CommandObject):
    """Handles /webcams command with subcommands."""
    args = command.args.split() if command.args else []
    
    if not args:
        # Show help/usage
        help_text = (
            "<b>📸 Windy Webcams Commands:</b>\n\n"
            "• <code>/webcams city [name]</code> - Get a live webcam for a city.\n"
            "• <code>/webcams nearby</code> - Get webcams near your location.\n"
            "• <code>/webcams country [code]</code> - List webcams in a country (e.g., US, DE).\n"
            "• <code>/webcams category [cat]</code> - List webcams in a category.\n"
            "• <code>/webcams id [ID]</code> - Get details for a specific webcam.\n"
            "• <code>/webcams list</code> - List popular webcams.\n"
            "• <code>/webcams categories</code> - List available categories.\n"
            "• <code>/webcams countries</code> - List available countries.\n"
            "• <code>/webcams regions [country]</code> - List regions.\n"
            "• <code>/webcams continents</code> - List continents.\n"
        )
        await message.answer(help_text)
        return

    subcommand = args[0].lower()
    
    if subcommand == "city":
        if len(args) < 2:
            await message.answer("Please provide a city name: <code>/webcams city London</code>")
            return
        
        city_query = " ".join(args[1:])
        msg = await message.answer(f"🔍 Searching for webcams in {city_query}...")
        
        # 1. Geocode
        weather_data = await get_weather(city_name=city_query)
        if not weather_data:
            await msg.edit_text(f"❌ Could not find location: {city_query}")
            return
            
        lat = weather_data.get("coord", {}).get("lat")
        lon = weather_data.get("coord", {}).get("lon")
        
        # 2. Search nearby
        # Radius 30km
        webcams_data = await get_webcams_list(nearby=f"{lat},{lon},30", limit=1)
        
        if webcams_data and webcams_data.get("webcams"):
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
            await msg.edit_text(f"❌ No webcams found near {city_query}.")

    elif subcommand == "nearby":
        # Request location
        # This part requires a separate handler for location or inline button.
        # For simplicity in this command, we'll ask user to share location.
        # But we can check if the message itself has location (unlikely for a command unless forwarded)
        # So we'll prompt.
        
        builder = InlineKeyboardBuilder()
        builder.button(text="📍 Share Location", callback_data="webcams_nearby_trigger")
        await message.answer("Click to find webcams near you:", reply_markup=builder.as_markup())

    elif subcommand == "list" or subcommand == "country" or subcommand == "category":
        # Generic list handler
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

    elif subcommand == "id":
        if len(args) < 2:
            await message.answer("Usage: <code>/webcams id [ID]</code>")
            return
        
        cam_id = args[1]
        data = await get_webcam_details(cam_id)
        
        if data:
            # The structure for details might be directly the webcam object or {webcam: {...}}?
            # API docs say /webcams/{id} returns the webcam object directly or wrapped?
            # Let's assume standard Windy response wrapper usually has the object or list.
            # Usually /webcams returns {webcams: []}. /webcams/{id} might return the object directly?
            # Actually standard API V3 responses are often just the data. 
            # Let's handle both.
            cam = data if "webcamId" in data else data.get("webcam") # fallback
            
            if not cam: 
                 # Maybe it returned a list of 1?
                 if data.get("webcams"):
                     cam = data["webcams"][0]
            
            if cam:
                title = cam.get("title", "Unknown")
                images = cam.get("images", {}).get("current", {})
                preview_url = images.get("preview")
                
                player = cam.get("player", {})
                day = player.get("day", {}).get("embed")
                live = player.get("live", {}).get("embed")
                player_link = live or day or ""
                
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
        else:
            await message.answer("Failed to fetch webcam details.")

    elif subcommand == "categories":
        data = await get_categories()
        if data:
            # data is usually a list of categories
            cats = [c.get("id") for c in data if isinstance(c, dict)] if isinstance(data, list) else []
            # Or maybe data['categories']?
            # Let's assume it might be a list based on "Returns a list of available categories".
            # If wrapped:
            if isinstance(data, dict) and "categories" in data:
                cats = [c.get("id") for c in data["categories"]]
            
            if cats:
                await message.answer(f"<b>Available Categories:</b>\n{', '.join(cats)}")
            else:
                await message.answer(f"No categories found or unexpected format: {str(data)[:100]}")
        else:
            await message.answer("Failed to fetch categories.")

    elif subcommand == "countries":
        data = await get_countries()
        if data:
            # simple list of codes?
            # "Returns a list of country codes."
            countries = []
            if isinstance(data, list):
                countries = [c.get("id", c.get("code")) for c in data]
            elif isinstance(data, dict) and "countries" in data:
                countries = [c.get("id", c.get("code")) for c in data["countries"]]
                
            if countries:
                # Truncate if too long
                shown = countries[:50]
                text = f"<b>Countries ({len(countries)}):</b>\n{', '.join(shown)}"
                if len(countries) > 50:
                    text += "..."
                await message.answer(text)
            else:
                await message.answer("No countries found.")
        else:
            await message.answer("Failed to fetch countries.")

    elif subcommand == "regions":
        country_code = args[1] if len(args) > 1 else None
        data = await get_regions(country_code)
        if data:
            regions = []
            if isinstance(data, list):
                regions = [r.get("id", r.get("name")) for r in data]
            elif isinstance(data, dict) and "regions" in data:
                regions = [r.get("id", r.get("name")) for r in data["regions"]]
            
            if regions:
                shown = regions[:50]
                text = f"<b>Regions:</b>\n{', '.join(shown)}"
                if len(regions) > 50:
                    text += "..."
                await message.answer(text)
            else:
                await message.answer("No regions found.")
        else:
            await message.answer("Failed to fetch regions.")

    elif subcommand == "continents":
        data = await get_continents()
        if data:
            continents = []
            if isinstance(data, list):
                continents = [c.get("id", c.get("name")) for c in data]
            elif isinstance(data, dict) and "continents" in data:
                continents = [c.get("id", c.get("name")) for c in data["continents"]]
                
            if continents:
                await message.answer(f"<b>Continents:</b>\n{', '.join(continents)}")
            else:
                await message.answer("No continents found.")
        else:
            await message.answer("Failed to fetch continents.")

    else:
        await message.answer("Unknown subcommand. Try <code>/webcams</code> for help.")

@router.callback_query(F.data == "webcams_nearby_trigger")
async def webcams_nearby_trigger(callback: types.CallbackQuery):
    """Trigger asking for location."""
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.button(text="📍 Share Location", request_location=True)
    await callback.message.answer(
        "Please share your location to find nearby webcams:",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await callback.answer()

