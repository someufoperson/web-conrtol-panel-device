import subprocess
ADB_PATH = r"C:\Users\myapo\Desktop\platform-tools\adb.exe"
"""
Функция get_devices должна запустить в цикле с интервалами по 5 секунд и записывать все устройства в
редиску, чтобы оттуда оперативно можно было подтянуть данные в front. Следовательно, должна быть отдельная
ручка для устройств
"""

def get_devices_from_adb():
    result = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True)
    result = result.stdout.split("\n")[1:]
    list_device = [x.split("\t")[0] for x in result if x != "" or x == "List of device attached"]
    return list_device
