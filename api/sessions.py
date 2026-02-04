import signal
from fastapi import APIRouter
import subprocess
from helper import data_gen
from db.models.sessions import SessionStatus, ConnectStatus
from pydantic import BaseModel
from db.requests.sessions import SessionReq as sr
from db.requests.devices import DevicesReq as dr
import datetime
import os
import asyncio
from helper.log import setup_logger

log = setup_logger()

class SessionCreateSchema(BaseModel):
    device_id: str

class SessionSchema(SessionCreateSchema):
    session_id: str
    connect_status: ConnectStatus
    session_status: SessionStatus
    outer_port: int
    inner_port: int
    login: str
    password: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

router = APIRouter(prefix="/sessions", tags=["Сессии"])

@router.post("")
async def create_session(device_id: str) -> dict:
    """
    Создание и запуск сессии (версия, в которой пока что сессии не вечные, переделаем на другой вариант)
    """
    path = os.getcwd()
    inner_port = await data_gen.inner_port_generator()
    outer_port = await data_gen.outer_port_generator()
    res = await sr.create_session(device_id=device_id, inner_port=inner_port, outer_port=outer_port)
    device = await dr.get_device_by_serial_number(serial_number=device_id)
    proc = subprocess.Popen([rf"{path}\venv\Scripts\python.exe",
                      rf"{path}\helper\web-scrcpy\app.py",
                      "--serial_number", device_id,
                      "--port", str(inner_port),
                      "--outer_port", str(outer_port),
                      "--link", str(res.id),
                      "--title", device.data,
                      "--login", str(res.login),
                      "--password", str(res.password)])
    await sr.insert_pid(res.id, proc.pid)
    await asyncio.sleep(10)
    log.info(f"Администратором была создана сессия {res.id} для устройства {device.serial_number}")
    return {"session_id": res.id,
            "link": f"http://127.0.0.1:{outer_port}/{res.id}",
            "login": str(res.login),
            "password": str(res.password),
            "link_autologin":f"http://{res.login}:{res.password}@127.0.0.1:{outer_port}/{res.id}",
            "procid": proc.pid}

@router.patch("/{session_id}/kill/")
async def update_session_status_deactivated_by_session_id(session_id: str, pid: int):
    """
    Убийство сессии
    """
    os.kill(pid, signal.SIGTERM)
    await sr.update_session_active_by_session_id(session_id=session_id,
                                                 status=SessionStatus.EXPIRED)
    log.info(f"Администратором была отключена сессия {session_id}")
    return {"status": "ok"}

@router.patch("/{device_id}/status-active/")
async def update_session_status_active_by_session_id(session_id: str):
    """
    Изменение статуса активности
    """
    await sr.update_session_active_by_session_id(session_id=session_id,
                                                 status=SessionStatus.ACTIVE)
    return {"status": "ok"}

@router.get("")
async def get_all_sessions():
    """
    Получить все сессии
    """
    res = await sr.get_all_sessions()
    return res

@router.get("/{session_id}")
async def get_session_by_session_id(session_id: str):
    """
    Получить информацию о конкретной сессии
    """
    res = await sr.get_session_by_id(session_id=session_id)
    return res

@router.patch("/{session_id}/connect/")
async def update_connect_status_by_session_id(session_id: str):
    """
    Изменить статус коннекта сессии (при подключении к сокету) - для автоматической смены статуса
    """
    await sr.update_session_connect_by_session_id(session_id=session_id,
                                                  status=ConnectStatus.CONNECTED)
    return {"status": "ok"}

@router.patch("/{session_id}/disconnect")
async def update_disconnect_status_by_session_id(session_id: str):
    """
    Изменить статус коннекта сессии (при подключении к сокету) - для автоматической смены статуса
    """
    await sr.update_session_connect_by_session_id(session_id=session_id,
                                                  status=ConnectStatus.DISCONNECTED)
    return {"status": "ok"}