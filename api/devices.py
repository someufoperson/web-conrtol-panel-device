from http import HTTPStatus
import redis
from fastapi import APIRouter, HTTPException
from db.models.devices import DeviceStatus, BusyStatus
from pydantic import BaseModel, ConfigDict
from db.requests.devices import DevicesReq as dr
from helper.adb_helper import get_devices_from_adb
import requests

class DeviceCreateSchema(BaseModel):
    serial_number: str
    data: str

    class Config:
        orm = True

class DeviceSchema(DeviceCreateSchema):
    status_online: DeviceStatus
    status_busy: BusyStatus

router = APIRouter(prefix="/devices", tags=["Устройства"])

@router.get("",
            summary="Получить все устройства в базе данных",
            )
async def get_all_devices() -> list[DeviceSchema]:
    """
    Получить список всех устройств, записанных в базе данных и их статусы
    """
    res = await dr.get_all_devices()
    return res

@router.get("/get-all-devices/",
            summary="Получить все устройства, которые видит ADB")
async def get_all_conn_devices() -> None:
    """
    Получить список всех устройств, которые подключены по USB и пробиваются в adb
    """
    res = get_devices_from_adb()
    return res

@router.get("/get-unsaved-devices/",
            summary="Получить все устройства, которые видит ADB и они не сохранены в базе данных")
async def get_unsaved_devices() -> set:
    cr = redis.Redis(host="localhost", port=6379, db=0)
    return cr.smembers("devices")

@router.post("/create/",
             summary="Создание устройства")
async def create_device(device: DeviceCreateSchema):
    """
    serial_number - серийный номер устройства, data - ФИО
    """
    devices = get_devices_from_adb()
    if device.serial_number not in devices:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail="устройство не найдено в списке подключенных к пк (используется adb)")
    result = await dr.create_device(serial_number=device.serial_number, data=device.data)
    if not result:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail="Устройство уже добавлено в базу данных")
    device = await dr.get_device_by_serial_number(serial_number=device.serial_number)
    return {"status": True, "new_device": device}

@router.get("/get-all-active-devices/")
async def get_all_active_devices() -> list[DeviceSchema]:
    """
    Метод на доработке
    """
    res = await dr.get_all_active_devices()
    return res

@router.get("/{device_id}/")
async def get_device_by_id(device_id: str) -> DeviceSchema:
    """
    Получить информацию об устройстве - метод на доработке
    """
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-busy/")
async def update_status_busy_by_id(device_id: str) -> DeviceSchema:
    """
    Обновить статус занятости (занят)
    """
    await dr.edit_status_busy_by_serial_number(serial_number=device_id,
                                               busy_status=BusyStatus.BUSY)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-free/")
async def update_status_free_by_id(device_id: str) -> DeviceSchema:
    """
    Обновить статус занятости (свободен)
    """
    await dr.edit_status_busy_by_serial_number(serial_number=device_id,
                                               busy_status=BusyStatus.FREE)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-online/")
async def update_status_online_by_id(device_id: str) -> DeviceSchema:
    """
    Обновить статус онлайна (онлайн) - метод для автоматического управления
    """
    await dr.edit_status_online_by_serial_number(serial_number=device_id,
                                                 status_online=DeviceStatus.ONLINE)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-offline/")
async def update_status_offline_by_id(device_id: str) -> DeviceSchema:
    """
    Обновить статус онлайна (офлайн) - метод для автоматического управления
    """
    await dr.edit_status_online_by_serial_number(serial_number=device_id,
                                                 status_online=DeviceStatus.OFFLINE)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res