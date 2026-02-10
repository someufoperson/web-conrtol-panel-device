from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from core.config import TGBotSettings
import asyncio

bot = Bot(token=TGBotSettings.TG_BOT_TOKEN,
          default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

async def main():
    # dp.include_routers(general_router, reg_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())