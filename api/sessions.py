import signal
from http import HTTPStatus
import requests
from fastapi import APIRouter, HTTPException
import subprocess
from helper import data_gen
from db.models.sessions import SessionStatus, ConnectStatus
from pydantic import BaseModel
from db.requests.sessions import SessionReq as sr
from db.requests.devices import DevicesReq as dr
import datetime
import os
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

@router.get("", summary="Получить все сессии")
async def get_all_sessions():
    """
    Получить все сессии
    """
    res = await sr.get_all_sessions()
    return res

@router.post("", summary="Создать сессию")
async def create_session(device_id: str) -> dict:
    """
    Создание и запуск сессии (версия, в которой пока что сессии не вечные, переделаем на другой вариант)
    """
    inner_port = await data_gen.inner_port_generator()
    outer_port = await data_gen.outer_port_generator()
    res = await sr.create_session(device_id=device_id, inner_port=inner_port, outer_port=outer_port)
    if not res:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail="Сессия для устройства уже создана")
    device = await dr.get_device_by_serial_number(serial_number=device_id)
    log.info(f"Администратором была создана сессия {res.id} для устройства {device.serial_number}")
    start = await up_socket_now(str(res.id))
    return {"session_id": res.id,
            "link": f"http://127.0.0.1:{outer_port}/{res.id}",
            "login": str(res.login),
            "password": str(res.password),
            "link_autologin":f"http://{res.login}:{res.password}@127.0.0.1:{outer_port}/{res.id}",
            "procid": start["pid"]
        }

@router.post("/{session_id}/up/", summary="Поднять сессию по id")
async def up_socket(session_id: str):
    start = await up_socket_now(session_id)
    return {"session_id": start["id"],
            "link": f"http://127.0.0.1:{start['outer_port']}/{start['id']}",
            "login": str(start['login']),
            "password": str(start['password']),
            "link_autologin":f"http://{start['login']}:{start['password']}@127.0.0.1:{start['outer_port']}/{start['id']}",
            "procid": start["pid"]
        }


@router.post("/down/", summary="Отключит ВСЕ сессии")
async def down_all_socket():
    await sr.down_all_session()
    return {"session": "killed"}

@router.patch("/{session_id}/kill/", summary="Отключить одну сессию")
async def update_session_status_deactivated_by_session_id(session_id: str):
    """
    Убийство сессии
    """
    session = await sr.get_session_by_id(session_id=session_id)
    os.kill(session.pid, signal.SIGTERM)
    await sr.update_session_active_by_session_id(session_id=session_id,
                                                 status=SessionStatus.NOT_ACTIVE)
    log.info(f"Администратором была деактивирована сессия {session_id}")
    return {"status": "ok"}

@router.patch("/{device_id}/status-active/")
async def update_session_status_active_by_session_id(session_id: str):
    """
    Изменение статуса активности
    """
    await sr.update_session_active_by_session_id(session_id=session_id,
                                                 status=SessionStatus.ACTIVE)
    return {"status": "ok"}



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

async def up_socket_now(session_id: str):
    path = os.getcwd()
    res = await sr.get_session_by_id(session_id=session_id)
    device = await dr.get_device_by_serial_number(serial_number=res.device_id)
    proc = subprocess.Popen([rf"{path}\venv\Scripts\python.exe",
                      rf"{path}\helper\web-scrcpy\app.py",
                      "--serial_number", res.device_id,
                      "--port", str(res.inner_port),
                      "--outer_port", str(res.outer_port),
                      "--link", str(res.id),
                      "--title", device.data,
                      "--login", str(res.login),
                      "--password", str(res.password)])
    await sr.insert_pid(res.id, proc.pid)
    log.info(f"Администратором была активирована сессия {res.id}")
    url = f"http://127.0.0.1:{res.outer_port}/{res.id}/check-health"
    while True:
        try:
            requests.get(url, timeout=5)
            break
        except:
            pass
    return {"pid": proc.pid,
            "login": res.login,
            "password": res.password,
            "outer_port": res.outer_port,
            "inner_port": res.inner_port,
            "id": res.id}