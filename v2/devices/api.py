import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from typing import Annotated
from core.redis_client import get_redis_connection
from devices.models import DeviceStatus, ConnectionStatus, SessionStatus
from devices.schemas import DeviceSchema, DeviceCreateSchema
from devices.repository import DeviceRepo
from core.database import get_async_session
from core.subprocess_helper import get_devices_from_adb
from devices.services import up_socket_now, down_socket_now


router = APIRouter(
    prefix="/v1/devices",
    tags=["Устройства"]
)

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]

@router.get("/all-in-base",
            summary="Возвращает полную информацию об устройствах в базе данных",
            status_code=status.HTTP_200_OK)
async def all_in_base(db: SessionDep) -> list[DeviceSchema]:
    return await DeviceRepo(db = db).get_all_devices()


@router.get("/device/{serial_number}",
            summary="Возвращает полную информацию об устройстве",
            status_code=status.HTTP_200_OK)
async def device(serial_number: str, db: SessionDep) -> DeviceSchema | None:
    result = await DeviceRepo(db = db).get_device_by_serial_number(serial_number = serial_number)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Устройства с указанным serial_number нет в базе данных")
    return DeviceSchema.model_validate(result)


@router.get("/adb-all-device",
            summary="Возвращает все устройства, подключенные к компьютеру при помощи команды ADB",
            status_code=status.HTTP_200_OK)
async def adb_all_device() -> list[str]:
    return get_devices_from_adb()


# @router.get("/all-unauthentic-device",
#             summary="Возвращает все устройства, не зарегистрированные в базе данных",
#             status_code=status.HTTP_200_OK)
# async def all_unauthentic_device() -> list[str]:
#     ...


@router.post("/create",
             summary="Создать запись об устройство в базе данных",
             status_code=status.HTTP_201_CREATED)
async def create(device_create: DeviceCreateSchema, db: SessionDep) -> DeviceSchema | dict:
    try:
        new_device = await DeviceRepo(db = db).create_device(device_create)
        return new_device
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/edit-label/{serial_number}",
              summary="Обновить ФИО закреплённое за устройством",
              status_code=status.HTTP_200_OK)
async def edit_label(serial_number: str,
                     label: str,
                     db: SessionDep) -> DeviceCreateSchema | None:
    result = await DeviceRepo(db = db).update_device(serial_number = serial_number, label = label)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Устройства с таким serial_number не существует")
    return DeviceCreateSchema.model_validate(result)


@router.patch("/update-status/online/{serial_number}/online",
              summary="Сервисный метод - не для ручного использования, обновляет статус устройства на online",
              status_code=status.HTTP_200_OK)
async def update_status_online(serial_number: str, db: SessionDep) -> DeviceSchema | None:
    result = await DeviceRepo(db = db).update_device(serial_number = serial_number,
                                                     status_device = DeviceStatus.ONLINE)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Устройства с таким serial_number не существует")
    return DeviceSchema.model_validate(result)


@router.patch("/update-status/online/{serial_number}/offline",
              summary="Сервисный метод - не для ручного использования, обновляет статус устройства на offline",
              status_code=status.HTTP_200_OK)
async def update_status_offline(serial_number: str, db: SessionDep) -> DeviceSchema | None:
    result = await DeviceRepo(db = db).update_device(serial_number = serial_number,
                                                     status_device = DeviceStatus.OFFLINE)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Устройства с таким serial_number не существует")
    return DeviceSchema.model_validate(result)


@router.patch("/update-status/connect/{serial_number}/connect",
              summary="Сервисный метод - не для ручного использования, обновляет статус подключения к устройству",
              status_code=status.HTTP_200_OK)
async def update_status_connect(serial_number: str, db: SessionDep) -> DeviceSchema | None:
    result = await DeviceRepo(db = db).update_device(serial_number = serial_number,
                                                     connection_status = ConnectionStatus.CONNECTED)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Устройства с таким serial_number не существует")
    return DeviceSchema.model_validate(result)


@router.patch("/update-status/connect/{serial_number}/disconnect",
              summary="Сервисный метод - не для ручного использования, обновляет статус отключен от устройства",
              status_code=status.HTTP_200_OK)
async def update_status_disconnect(serial_number: str, db: SessionDep) -> DeviceSchema | None:
    result = await DeviceRepo(db = db).update_device(serial_number = serial_number,
                                                     connection_status = ConnectionStatus.DISCONNECTED)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Устройства с таким serial_number не существует")
    return DeviceSchema.model_validate(result)


@router.patch("/update-status/session/{serial_number}/active",
              summary="Поднять сервер с устройством")
async def update_status_active(serial_number: str, db: SessionDep):
    device_full = await DeviceRepo(db = db).get_device_by_serial_number(serial_number = serial_number)
    pid = await up_socket_now(device_full)
    res = await DeviceRepo(db = db).update_device(serial_number = serial_number,
                                                  session_status = SessionStatus.ACTIVE,
                                                  pid = pid)
    return DeviceSchema.model_validate(res)


@router.patch("/update-status/session/{serial_number}/inactive",
              summary="Отключить сервер с устройством",
              status_code=status.HTTP_200_OK)
async def update_status_inactive(serial_number: str, db: SessionDep) -> DeviceSchema | None:
    device_full = await DeviceRepo(db = db).get_device_by_serial_number(serial_number = serial_number)
    await down_socket_now(device_full)
    res = await DeviceRepo(db = db).update_device(serial_number = serial_number,
                                                  session_status = SessionStatus.INACTIVE,
                                                  connection_status = ConnectionStatus.DISCONNECTED,
                                                  pid = None)
    return DeviceSchema.model_validate(res)


@router.post("/all-device-active",
             summary="Поднять сервера для управления для всех устройств \
             ❗️МОЖЕТ ЗАНЯТЬ МНОГО ВРЕМЕНИ, ПОКА СЕССИ \
             ПОДНИМАЮТСЯ РАБОТАТЬ С ПАНЕЛЬЮ НЕ ПОЛУЧИТСЯ")
async def all_device_active(db: SessionDep) -> dict:
    devices = await DeviceRepo(db = db).get_all_devices()
    for dev in devices:
        await update_status_active(dev.serial_number, db)
    return {"status": "success"}


@router.post("/all-device-inactive",
             summary="Отключить сервера для управления для всех устройств")
async def all_device_inactive(db: SessionDep) -> dict:
    devices = await DeviceRepo(db = db).get_device_by_session_status()
    for dev in devices:
        await update_status_inactive(dev.serial_number, db)
    return {"status": "success"}


@router.get("/all-devices-online",
            summary="Получить все устройства онлайн в базе данных")
async def all_devices_online(db: SessionDep) -> list[str]:
    return await DeviceRepo(db = db).get_all_online_devices()


@router.get("/all-not-auth-device",
            summary="Получить все незарегистрированные устройства")
async def all_not_auth_device():
    cr = redis.Redis(host="localhost", port=6379, db=0) #TODO: сделать людской коннект к редиске
    return cr.smembers("devices")