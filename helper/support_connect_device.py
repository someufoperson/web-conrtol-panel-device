import asyncio
import subprocess
import asyncio
from db.models.devices import DeviceStatus
from db.requests.devices import DevicesReq as dr
import redis
import requests

async def device_connect():
    requests.post("http://127.0.0.1:8000/sessions/down/")
    while True:
        cr = redis.Redis(host="localhost", port=6379, db=0)
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        result = result.stdout.split("\n")[1:]
        list_device = [x.split("\t")[0] for x in result if x != "" or x == "List of device attached"]
        res = await dr.get_all_online_devices()
        for device in res:
            if device.serial_number in list_device:
                await dr.edit_status_online_by_serial_number(serial_number=device.serial_number,
                                                             status_online=DeviceStatus.ONLINE)
                list_device.remove(device.serial_number)
                cr.srem("devices", device.serial_number)
            elif device.serial_number not in list_device:
                await dr.edit_status_online_by_serial_number(serial_number=device.serial_number,
                                                             status_online=DeviceStatus.OFFLINE)
        if list_device:
            cr.sadd("devices", *list_device)
        await asyncio.sleep(1)

if "__main__" == __name__:
    asyncio.run(device_connect())