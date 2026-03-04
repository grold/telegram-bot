import logging
import aiohttp
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command, CommandObject

router = Router()
logger = logging.getLogger(__name__)

# Free Exchangerate API (no key required)
# returns rates relative to the base currency
API_URL_TEMPLATE = "https://open.er-api.com/v6/latest/{}"

@router.message(Command("rate"))
async def cmd_rate(message: types.Message, command: CommandObject):
    """
    Handles the /rate command.
    Usage:
      /rate - Shows default rates (USD, EUR, JPY to RUB)
      /rate CUR1-CUR2 - Shows rate for CUR1 to CUR2
      /rate CUR1 CUR2 - Same as above
    """
    args = command.args
    
    try:
        # Scenario 1: Custom currency pair
        if args:
            # parsing "CUR1-CUR2" or "CUR1 CUR2"
            parts = args.replace("-", " ").split()
            if len(parts) != 2:
                await message.answer("⚠️ Usage: <code>/rate USD-EUR</code> or <code>/rate USD EUR</code>")
                return
            
            base_cur = parts[0].upper()
            target_cur = parts[1].upper()
            
            # Basic validation (3-4 chars usually)
            if not (2 <= len(base_cur) <= 5) or not (2 <= len(target_cur) <= 5):
                 await message.answer("⚠️ Invalid currency codes.")
                 return

            url = API_URL_TEMPLATE.format(base_cur)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})
                        
                        if target_cur in rates:
                            rate = rates[target_cur]
                            date_str = data.get("time_last_update_utc", "")[:16] # simplified date
                            
                            await message.answer(
                                f"<b>💱 Exchange Rate ({base_cur} -> {target_cur}):</b>\n"
                                f"• 1 {base_cur} = <code>{rate:.4f}</code> {target_cur}\n"
                                f"<small>Date: {date_str}</small>"
                            )
                        else:
                            await message.answer(f"⚠️ Currency <code>{target_cur}</code> not found in rates for {base_cur}.")
                    else:
                        logger.error(f"Exchange API error: {response.status}")
                        await message.answer("⚠️ Error fetching rates from API.")
                        
        # Scenario 2: Default rates (USD, EUR, JPY -> RUB)
        else:
            # We use RUB as base to get all relevant pairs in one request
            # 1 RUB = X USD  =>  1 USD = 1/X RUB
            base_cur = "RUB"
            url = API_URL_TEMPLATE.format(base_cur)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})
                        date_str = data.get("time_last_update_utc", "")[:16]
                        
                        response_parts = [f"<b>💰 Exchange Rates (Base: RUB):</b>\n"]
                        
                        targets = ["USD", "EUR", "JPY", "CNY"] # Added CNY as it's common now
                        
                        for code in targets:
                            if code in rates:
                                val = rates[code]
                                if val > 0:
                                    inverse = 1 / val
                                    response_parts.append(f"• <b>{code}/RUB:</b> <code>{inverse:.2f}</code>")
                        
                        response_parts.append("\n<i>Source: open.er-api.com</i>")
                        response_parts.append(f"<small>Updated: {date_str}</small>")
                        response_parts.append("\n<i>Valekoo reports</i>")
                        response_parts.append('<a href="https://t.me/supopochi">supopochi</a>')
                        
                        await message.answer("\n".join(response_parts))
                    else:
                         logger.error(f"Exchange API error: {response.status}")
                         await message.answer("⚠️ Service unavailable.")

    except Exception as e:
        logger.exception(f"Error in cmd_rate: {e}")
        await message.answer(f"⚠️ An error occurred: <code>{e}</code>")
