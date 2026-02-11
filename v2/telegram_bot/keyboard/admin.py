from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def list_device_kb(list_device: list):
    keyboard = InlineKeyboardBuilder()
    for device in list_device:
        status_device = "🟢онлайн" if device["status_device"] == "ONLINE" else "🔴офлайн"
        session_status = "🟢сессия" if device["session_status"] == "ACTIVE" else"🔴сессия"
        keyboard.add(InlineKeyboardButton(text=f"{status_device}|{device["label"]}|{session_status}",
                                          callback_data=f"sn:{device['serial_number']}:{device['session_status']}"))
    keyboard.add(InlineKeyboardButton(text="🔄Обновить", callback_data="reload_list"))
    return keyboard.adjust(1).as_markup()


async def list_for_copy_kb(list_device: list):
    keyboard = InlineKeyboardBuilder()
    for device in list_device:
        if device["session_status"] == "ACTIVE":
            status_device = "🟢онлайн" if device["status_device"] == "ONLINE" else "🔴офлайн"
            keyboard.add(InlineKeyboardButton(text=f"{status_device}|{device["label"]}",
                                              copy_text=CopyTextButton(text=f"https://money-maker.shop/{device['serial_number']}")))
    keyboard.add(InlineKeyboardButton(text="🔄Обновить", callback_data="reload_copy"))
    return keyboard.adjust(1).as_markup()