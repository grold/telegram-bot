import logging
import asyncio
from uuid import uuid4
from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from handlers.weather import get_weather, format_weather_message

router = Router()
logger = logging.getLogger(__name__)

# Load cities from file at startup
try:
    with open("cities.txt", "r") as f:
        CITIES = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    logger.warning("cities.txt not found. Autocompletion will be disabled.")
    CITIES = []

@router.inline_query()
async def inline_weather_handler(inline_query: types.InlineQuery):
    """Handles inline queries for weather with autocompletion."""
    query = inline_query.query.strip()
    results = []

    if not query and not inline_query.location:
        # If query is empty and no location provided, show an instructional message
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Enter a city name for weather",
                input_message_content=InputTextMessageContent(
                    message_text="Please type a city name after the bot's username or use the location button."
                )
            )
        )
        await inline_query.answer(results, cache_time=300)
        return

    # --- Location Handling ---
    if inline_query.location:
        lat = inline_query.location.latitude
        lon = inline_query.location.longitude
        data = await get_weather(lat=lat, lon=lon)
        
        if data:
            location_name = data.get('name', 'Your Location')
            full_weather_report = format_weather_message(data)
            
            # Create a summary for the description
            weather_list = data.get("weather", [{}])
            condition = weather_list[0].get("description", "Unknown").capitalize()
            temp = data.get("main", {}).get("temp")
            description_summary = f"{temp}°C, {condition}"

            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f"Weather at {location_name}",
                    description=description_summary,
                    input_message_content=InputTextMessageContent(
                        message_text=full_weather_report,
                        parse_mode="HTML"
                    )
                )
            )
            # If we only want to return location results when the user presses the button
            if not query:
                await inline_query.answer(results, cache_time=60)
                return

    # --- Autocompletion Logic ---
    matching_cities = [city for city in CITIES if city.lower().startswith(query.lower())][:5]
    
    if matching_cities:
        # Fetch weather for all matching cities concurrently
        tasks = [get_weather(city_name=city) for city in matching_cities]
        weather_results = await asyncio.gather(*tasks)

        for city, data in zip(matching_cities, weather_results):
            if data:
                # Create a summary for the description
                weather_list = data.get("weather", [{}])
                condition = weather_list[0].get("description", "Unknown").capitalize()
                temp = data.get("main", {}).get("temp")
                description_summary = f"{temp}°C, {condition}"
                
                # Use the full detailed message for the content
                full_weather_report = format_weather_message(data)
                
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=city,
                        description=description_summary,
                        input_message_content=InputTextMessageContent(
                            message_text=full_weather_report,
                            parse_mode="HTML"
                        )
                    )
                )
    else:
        # If no suggestions, fall back to searching for the exact query
        data = await get_weather(city_name=query)
        if data:
            full_weather_report = format_weather_message(data)
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f"Weather in {data.get('name', query)}",
                    input_message_content=InputTextMessageContent(
                        message_text=full_weather_report,
                        parse_mode="HTML"
                    )
                )
            )
            
    if not results:
        # If still no results, show a "not found" message
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"City not found: '{query}'",
                input_message_content=InputTextMessageContent(
                    message_text=f"Sorry, I couldn't find the weather for '{query}'."
                )
            )
        )

    await inline_query.answer(results, cache_time=60)
