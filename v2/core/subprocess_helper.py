import os
import signal
import subprocess
import warnings
from core.config import redis_settings, adb_settings

def start_redis_docker():
    warnings.warn(
        "Данный метод используется только для dev. \
                Дальнейший старт приложения будет осуществляться с docker-compose",
        DeprecationWarning,
        stacklevel=1
    )
    subprocess.run(["docker",
                    "run",
                    "-d",
                    "--name",
                    "redis",
                    "-p",
                    f"{redis_settings.REDIS_PORT}:{redis_settings.REDIS_PORT}",
                    "redis:latest"])

def get_devices_from_adb():
    result = subprocess.run([adb_settings.ADB_PATH, "devices"], capture_output=True, text=True)
    result = result.stdout.split("\n")[1:]
    list_device = [x.split("\t")[0] for x in result if x != "" or x == "List of device attached"]
    return list_device

def server_up(cmd: list) -> int:
    proc = subprocess.Popen(cmd)
    return proc.pid

def server_down(pid: int) -> None:
    os.kill(pid, signal.SIGTERM)

def status_online_helper():
    subprocess.Popen([fr"{os.getcwd()}\venv\Scripts\python.exe", fr"{os.getcwd()}\core\device_connecting.py"])