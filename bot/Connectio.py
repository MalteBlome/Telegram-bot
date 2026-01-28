import asyncio
from telegram import Bot

TOKEN = "8596653896:AAFqU1kAhw-fMrY-6xikAyz8j69s1fUlyvo"
bot = Bot(TOKEN)

async def test_bot():
    info = await bot.get_me()
    print(info)

    # asyncio.run() führt die Coroutine aus
asyncio.run(test_bot())