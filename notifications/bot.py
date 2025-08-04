import asyncio
import os
import telegram
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


async def main():
    bot = telegram.Bot(TOKEN)
    async with bot:
        print(await bot.get_me())


if __name__ == "__main__":
    asyncio.run(main())
