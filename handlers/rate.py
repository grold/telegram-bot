import logging
import asyncio
import aiohttp
from aiogram import Router, types
from aiogram.filters import Command

router = Router()
logger = logging.getLogger(__name__)

RBC_TICKERS = {
    "USD": "USDRUB",
    "EUR": "EURRUB",
    "JPY": "JPYRUB"
}

BASE_URL = "https://quote.rbc.ru/v2/publisher/ticker/item/"

async def fetch_rbc_rate(session, currency, ticker):
    """Fetches a single rate from RBC API."""
    url = f"{BASE_URL}{ticker}"
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                # RBC API v2 structure: data['data']['last_price']
                last_price = data.get('data', {}).get('last_price')
                if last_price:
                    return currency, last_price
                else:
                    logger.error(f"RBC API returned 200 but last_price missing for {currency}: {data}")
            else:
                logger.error(f"RBC API for {currency} returned status {response.status}")
    except Exception as e:
        logger.exception(f"Error fetching RBC rate for {currency}")
    
    return currency, None

@router.message(Command("rate"))
async def cmd_rate(message: types.Message):
    """Handles the /rate command."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_rbc_rate(session, cur, ticker) for cur, ticker in RBC_TICKERS.items()]
        results = await asyncio.gather(*tasks)
    
    rates = dict(results)
    
    response_parts = ["""<b>💰 Current Exchange Rates (RBC.ru):</b>\n"""]
    
    found_any = False
    for currency in ["USD", "EUR", "JPY"]:
        val = rates.get(currency)
        if val is not None:
            response_parts.append(f"""• <b>{currency}/RUB:</b> <code>{val:.2f}</code>""")
            found_any = True
        else:
            response_parts.append(f"""• <b>{currency}/RUB:</b> <i>Data unavailable</i>""")
    
    if not found_any:
        await message.answer("""⚠️ Sorry, I couldn't fetch any exchange rates from RBC at the moment.""")
        return

    response_parts.append("""\n<i>Valekoo reports</i>""")
    
    await message.answer("\n".join(response_parts))
