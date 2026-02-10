from aiogram import F, Bot, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command


router = Router()


@router.message(Command('active_device'))
async def active_device(m: Message):
    ...