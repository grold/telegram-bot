import logging
import aiohttp
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command

router = Router()
logger = logging.getLogger(__name__)

# Reliable JSON mirror of Central Bank of Russia (cbr.ru) data
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

@router.message(Command("rate"))
async def cmd_rate(message: types.Message):
    """Handles the /rate command using CBR data."""
    try:
        # Disable SSL verification to prevent "certificate verify failed" errors in some envs
        # We use a custom connector for this.
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(CBR_API_URL, timeout=15) as response:
                if response.status == 200:
                    # CBR mirror returns application/javascript sometimes, 
                    # so we tell aiohttp to skip strict content-type check.
                    data = await response.json(content_type=None)
                    valute = data.get("Valute", {})
                    date_str = data.get("Date", "")
                    
                    # Try to parse date for a cleaner display
                    try:
                        # CBR date format is usually ISO: 2026-03-04T11:30:00+03:00
                        date_obj = datetime.fromisoformat(date_str)
                        formatted_date = date_obj.strftime("%d.%m.%Y")
                    except (ValueError, TypeError):
                        formatted_date = date_str[:10] if date_str else "Unknown"

                    # Extract rates
                    usd = valute.get("USD", {})
                    eur = valute.get("EUR", {})
                    jpy = valute.get("JPY", {})
                    
                    response_parts = [f"<b>💰 Exchange Rates (CBR.ru {formatted_date}):</b>\n"]
                    
                    found_any = False
                    
                    # USD
                    if usd:
                        rate = usd.get("Value")
                        response_parts.append(f"• <b>USD/RUB:</b> <code>{rate:.2f}</code>")
                        found_any = True
                    
                    # EUR
                    if eur:
                        rate = eur.get("Value")
                        response_parts.append(f"• <b>EUR/RUB:</b> <code>{rate:.2f}</code>")
                        found_any = True
                        
                    # JPY (Note: CBR rate is usually per 100 Yen)
                    if jpy:
                        nominal = jpy.get("Nominal", 1)
                        rate = jpy.get("Value")
                        # Normalize to 1 JPY if nominal is not 1 (e.g., 100)
                        if nominal and nominal != 1:
                            rate = rate / nominal
                        response_parts.append(f"• <b>JPY/RUB:</b> <code>{rate:.2f}</code>")
                        found_any = True
                        
                    if not found_any:
                        await message.answer("⚠️ Sorry, I couldn't find the exchange rates in the response.")
                        return

                    response_parts.append("\n<i>Valekoo reports</i>")
                    response_parts.append('<a href="https://t.me/supopochi">supopochi</a>')
                    await message.answer("\n".join(response_parts))
                else:
                    logger.error(f"CBR API returned status {response.status}")
                    await message.answer(f"⚠️ Sorry, the exchange rate service returned an error (Status {response.status}).")
    except Exception as e:
        logger.exception(f"Error fetching exchange rates: {e}")
        # Return a more descriptive error to the user for now to help diagnosis
        await message.answer(f"⚠️ Sorry, an error occurred while fetching exchange rates: <code>{type(e).__name__}</code>")
