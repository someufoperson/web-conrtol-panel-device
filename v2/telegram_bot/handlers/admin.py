import asyncio

from aiogram import F, Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from telegram_bot.keyboard import admin as admin_keyboard
from core.config import tg_bot_settings
import requests


bot = Bot(token=tg_bot_settings.TG_BOT_TOKEN)


router = Router()


@router.message(Command('devices'))
async def active_device(m: Message):
    res = requests.get(f"http://127.0.0.1:8000/v1/devices/all-in-base")
    markup = await admin_keyboard.list_device_kb(res.json())
    await m.answer(text=
                    "Все устройства в базе данных, чтобы включить или отключить \
                    сервер для управления - нажмите на устройство",
                   reply_markup=markup)


@router.message(Command('start_all'))
async def start_all(m: Message):
    await m.answer(text="Начинаю запуск всех сессий")
    requests.post("http://127.0.0.1:8000/v1/devices/all-device-active", timeout=60)
    await m.answer(text="Все сессии запущены")


@router.message(Command('stop_all'))
async def stop_all(m: Message):
    await m.answer(text="Останавливаю все сессии")
    requests.post("http://127.0.0.1:8000/v1/devices/all-device-inactive")


@router.message(Command('for_copy'))
async def for_copy(m: Message):
    res = requests.get(f"http://127.0.0.1:8000/v1/devices/all-in-base")
    markup = await admin_keyboard.list_for_copy_kb(res.json())
    await m.answer(text="Устройства для копирования по нажатию на кнопку", reply_markup=markup)


@router.callback_query(F.data.startswith("reload_"))
async def reload_func(c: CallbackQuery):
    await c.answer()
    _, action = c.data.split("_")
    res = requests.get(f"http://127.0.0.1:8000/v1/devices/all-in-base")
    if action == "copy":
        markup = await admin_keyboard.list_for_copy_kb(res.json())
    elif action == "list":
        markup = await admin_keyboard.list_device_kb(res.json())
    await bot.edit_message_reply_markup(message_id=c.message.message_id, chat_id=c.message.chat.id, reply_markup=markup)


@router.callback_query(F.data.startswith("sn"))
async def update_status(c: CallbackQuery):
    _, serial_number, status = c.data.split(":")
    if status == "ACTIVE":
        requests.patch(f"http://127.0.0.1:8000/v1/devices/update-status/session/{serial_number}/inactive")
        text = "Отправлен запрос на отключение сессии"
    elif status == "INACTIVE":
        requests.patch(f"http://127.0.0.1:8000/v1/devices/update-status/session/{serial_number}/active")
        text="Процедура поднятия сервера занимает некоторое время, ожидайте обновления клавиатуры"
    await c.answer(text=text, show_alert=True)
    res = requests.get(f"http://127.0.0.1:8000/v1/devices/all-in-base")
    markup = await admin_keyboard.list_device_kb(res.json())
    await bot.edit_message_reply_markup(message_id=c.message.message_id, chat_id=c.message.chat.id, reply_markup=markup)