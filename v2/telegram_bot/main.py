from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from core.config import tg_bot_settings
from aiogram.types import BotCommand
from telegram_bot.handlers.admin import router
import asyncio

bot = Bot(token=tg_bot_settings.TG_BOT_TOKEN,
          default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

async def set_bot_commands():
    commands = [
        BotCommand(command="devices", description="📱Получить все устройства - для включения/выключения сессий"),
        BotCommand(command="start_all", description="🟢Запустить все сессии"),
        BotCommand(command="stop_all", description="🔴Остановить все сессии"),
        BotCommand(command="for_copy", description="🔗Список активных сессий для копирования ссылок при нажатии на кнопку")
    ]
    await bot.set_my_commands(commands)

async def main():
    dp.include_routers(router)
    await set_bot_commands()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())