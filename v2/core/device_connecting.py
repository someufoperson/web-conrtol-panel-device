import subprocess
import asyncio
import redis
import requests

async def device_connect():
    while True:
        cr = redis.Redis(host="localhost", port=6379, db=0)
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        result = result.stdout.split("\n")[1:]
        list_device = [x.split("\t")[0] for x in result if x != "" or x == "List of device attached"]
        res = requests.get(f"http://127.0.0.1:8000/v1/devices/all-devices-online")
        for device in res.json():
            if device in list_device:
                requests.patch(f"http://127.0.0.1:8000/v1/devices/update-status/online/{device}/online")
                list_device.remove(device)
                cr.srem("devices", device)
            elif device not in list_device:
                requests.patch(f"http://127.0.0.1:8000/v1/devices/update-status/online/{device}/offline")
        if list_device:
            cr.sadd("devices", *list_device)
        await asyncio.sleep(1)

if "__main__" == __name__:
    asyncio.run(device_connect())