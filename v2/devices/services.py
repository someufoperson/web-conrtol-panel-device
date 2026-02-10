
from devices.schemas import DeviceSchema
from core.subprocess_helper import server_up, server_down
from core.config import LinkSettings
import os
import requests

async def up_socket_now(device: DeviceSchema) -> int:
    path = os.getcwd()
    cmd = [rf"{path}\venv\Scripts\python.exe",
           rf"{path}\web-scrcpy\app.py",
           "--serial_number", device.serial_number,
           "--port", str(device.device_port),
           "--outer_port", str(device.flask_port),
           "--title", device.label]
    pid = server_up(cmd)
    url = f"http://127.0.0.1:{device.flask_port}/{device.serial_number}/check-health"
    while True:
        try:
            requests.get(url, timeout=5)
            break
        except:
            pass
    return pid

async def down_socket_now(device: DeviceSchema):
    server_down(device.pid)