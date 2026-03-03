import logging
import aiohttp
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
        async with aiohttp.ClientSession() as session:
            async with session.get(CBR_API_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    valute = data.get("Valute", {})
                    
                    # Extract rates
                    usd = valute.get("USD", {})
                    eur = valute.get("EUR", {})
                    jpy = valute.get("JPY", {})
                    
                    response_parts = ["<b>💰 Current Exchange Rates (CBR.ru):</b>\n"]
                    
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
                        if nominal != 1:
                            rate = rate / nominal
                        response_parts.append(f"• <b>JPY/RUB:</b> <code>{rate:.2f}</code>")
                        found_any = True
                        
                    if not found_any:
                        await message.answer("⚠️ Sorry, I couldn't find the exchange rates in the response.")
                        return

                    response_parts.append("\n<i>Valekoo reports</i>")
                    await message.answer("\n".join(response_parts))
                else:
                    logger.error(f"CBR API returned status {response.status}")
                    await message.answer("⚠️ Sorry, the exchange rate service is currently unavailable.")
    except Exception as e:
        logger.exception("Error fetching exchange rates")
        await message.answer("⚠️ Sorry, an error occurred while fetching exchange rates.")
