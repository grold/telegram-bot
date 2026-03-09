import logging
import aiohttp
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command, CommandObject

router = Router()
logger = logging.getLogger(__name__)

# Free Exchangerate API (no key required)
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
        if args:
            # Scenario 1: Custom currency pair
            parts = args.replace("-", " ").split()
            if len(parts) != 2:
                await message.answer("⚠️ Usage: <code>/rate USD-EUR</code> or <code>/rate USD EUR</code>")
                return
            
            base_cur = parts[0].upper()
            target_cur = parts[1].upper()
            
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
                            date_str = data.get("time_last_update_utc", "")[:16]
                            
                            await message.answer(
                                f"<b>💱 Exchange Rate ({base_cur} -> {target_cur}):</b>\n"
                                f"• 1 {base_cur} = <code>{rate:.4f}</code> {target_cur}\n"
                                f"Date: {date_str}"
                            )
                        else:
                            await message.answer(f"⚠️ Currency <code>{target_cur}</code> not found.")
                    else:
                        await message.answer("⚠️ API Error.")
                        
        else:
            # Scenario 2: Default rates
            base_cur = "RUB"
            url = API_URL_TEMPLATE.format(base_cur)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})
                        date_str = data.get("time_last_update_utc", "")[:16]
                        
                        response_parts = [f"<b>💰 Exchange Rates (Base: RUB):</b>"]
                        
                        targets = ["USD", "EUR", "JPY", "CNY"]
                        for code in targets:
                            if code in rates:
                                val = rates[code]
                                if val > 0:
                                    inverse = 1 / val
                                    response_parts.append(f"• <b>{code}/RUB:</b> <code>{inverse:.2f}</code>")
                        
                        response_parts.append(f"\n<i>Source: open.er-api.com</i>")
                        response_parts.append(f"Updated: {date_str}")
                        response_parts.append("\n<i>Valekoo reports</i>")
                        response_parts.append('<a href="https://t.me/supopochi">supopochi</a>')
                        
                        await message.answer("\n".join(response_parts))
                    else:
                         await message.answer("⚠️ Service unavailable.")

    except Exception as e:
        logger.exception(f"Error in cmd_rate: {e}")
        await message.answer(f"⚠️ An error occurred: <code>{type(e).__name__}</code>")
