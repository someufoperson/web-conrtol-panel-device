from fastapi import APIRouter
import subprocess
from db.models.sessions import SessionStatus, ConnectStatus
from pydantic import BaseModel
from db.requests.sessions import SessionReq as sr
from db.requests.devices import DevicesReq as dr
import datetime

class SessionCreateSchema(BaseModel):
    device_id: str

class SessionSchema(SessionCreateSchema):
    session_id: str
    connect_status: ConnectStatus
    session_status: SessionStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime

router = APIRouter(prefix="/sessions", tags=["Сессии"])

@router.post("")
async def create_session(device_id: str) -> dict:
    res = await sr.create_session(device_id=device_id)
    device = await dr.get_device_by_serial_number(serial_number=device_id)
    print(device)
    subprocess.Popen([r"C:\Users\myapo\Documents\Python\PythonProject\ADB_control_panel\venv\Scripts\python.exe", r"C:\Users\myapo\Documents\Python\PythonProject\ADB_control_panel\helper\web-scrcpy\app.py", "--serial_number", device_id, "--port", str(device.local_port), "--link", str(res)])
    return {"session_id": res, "link": f"http://127.0.0.1:5000/{res}"}

@router.patch("/{device_id}/status-deactive/")
async def update_session_status_deactive_by_session_id(session_id: str):
    await sr.update_session_active_by_session_id(session_id=session_id,
                                                 status=SessionStatus.EXPIRED)
    return {"status": "ok"}

@router.patch("/{device_id}/status-active/")
async def update_session_status_active_by_session_id(session_id: str):
    await sr.update_session_active_by_session_id(session_id=session_id,
                                                 status=SessionStatus.ACTIVE)
    return {"status": "ok"}

@router.get("")
async def get_all_sessions():
    res = await sr.get_all_sessions()
    return res

@router.get("/{session_id}")
async def get_session_by_session_id(session_id: str):
    res = await sr.get_session_by_id(session_id=session_id)
    return res

@router.patch("/{session_id}")
async def update_connect_status_by_session_id(session_id: str):
    await sr.update_session_connect_by_session_id(session_id=session_id,
                                                  status=ConnectStatus.CONNECTED)
    return {"status": "ok"}

@router.patch("/{session_id}")
async def update_disconnect_status_by_session_id(session_id: str):
    await sr.update_session_connect_by_session_id(session_id=session_id,
                                                  status=ConnectStatus.DISCONNECTED)
    return {"status": "ok"}