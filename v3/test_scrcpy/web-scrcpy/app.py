from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room  # Импортируем функции для комнат
from scrcpy import Scrcpy
import argparse
import queue
import subprocess
import socket
import random
from loguru import logger
import sys
from typing import Dict, Set, Optional

# ---------- Глобальные переменные (будут переопределены из cmd_args) ----------
ADB_PATH = "adb"
SCRCPY_SERVER_PATH = "web-scrcpy/scrcpy-server"
ALLOWED_DEVICES: Optional[Set[str]] = None
cmd_args = None  # будет установлен после парсинга

# ---------- Состояние сервера ----------
active_connections: Dict[str, dict] = {}   # serial -> {scrcpy, queue, task}
sid_to_device: Dict[str, str] = {}         # sid -> serial
room_clients: Dict[str, Set[str]] = {}     # serial -> set(sid)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*", binary=True)

# ---------- Вспомогательные функции ----------
def find_free_port() -> int:
    """Возвращает свободный порт в диапазоне 30000-40000."""
    while True:
        port = random.randint(30000, 40000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port

def is_device_available(serial: str) -> bool:
    """Проверяет, видит ли adb устройство с данным serial."""
    try:
        result = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        # пропускаем заголовок "List of devices attached"
        for line in lines[1:]:
            if line.strip() and serial in line and "device" in line:
                return True
        return False
    except Exception as e:
        logger.error(f"ADB devices check failed: {e}")
        return False

def video_send_task(serial: str):
    conn = active_connections.get(serial)
    if not conn:
        return
    q = conn['queue']
    logger.info(f"Video send task started for {serial}")
    while serial in active_connections:
        try:
            data = q.get(timeout=0.001)  # 1 мс
            # Проверяем, не накопилось ли много данных в очереди
            # Если да, пропускаем все, кроме последнего
            while not q.empty():
                data = q.get_nowait()    # берём последний кадр
            socketio.emit('video_data', data, room=serial)
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error sending video for {serial}: {e}")
    logger.info(f"Video send task stopped for {serial}")

# ---------- Маршруты Flask ----------
@app.route('/device/<serial_number>')
def device_page(serial_number):
    """Страница для конкретного устройства."""
    return render_template('index.html', title=f"Device {serial_number}")

@app.route('/check-health')
def check_health():
    return {"status": "ok"}

# ---------- События Socket.IO ----------
@socketio.on('connect')
def handle_connect(auth=None):  # Явно указываем параметр
    """Клиент подключается. Определяем устройство и запускаем scrcpy при необходимости."""
    global cmd_args
    serial = request.args.get('device')
    if not serial:
        logger.warning("Connect without device parameter")
        return False

    if ALLOWED_DEVICES and serial not in ALLOWED_DEVICES:
        logger.warning(f"Device {serial} not in allowed list")
        return False

    if not is_device_available(serial):
        logger.warning(f"Device {serial} not available via ADB")
        return False

    sid = request.sid
    sid_to_device[sid] = serial
    room_clients.setdefault(serial, set()).add(sid)

    if serial in active_connections:
        # Устройство уже запущено, просто добавляем клиента в комнату
        join_room(serial)  # Используем глобальную функцию, sid берётся из контекста
        logger.info(f"Client {sid} joined existing room for {serial}")
        return

    # Первый клиент – запускаем новый экземпляр scrcpy
    local_port = find_free_port()
    logger.info(f"Starting scrcpy for {serial} on port {local_port}")

    sc = Scrcpy(serial_number=serial, local_port=local_port,
                adb_path=ADB_PATH, server_path=SCRCPY_SERVER_PATH)

    q = queue.Queue()
    def video_callback(data):
        q.put(data)

    sc.scrcpy_start(video_callback, cmd_args.video_bit_rate)

    active_connections[serial] = {
        'scrcpy': sc,
        'queue': q,
        'task': socketio.start_background_task(video_send_task, serial)
    }

    join_room(serial)  # Добавляем клиента в комнату
    logger.info(f"New device {serial} started for client {sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Клиент отключается. Если комната опустела – останавливаем scrcpy."""
    sid = request.sid
    serial = sid_to_device.pop(sid, None)
    if not serial:
        return

    leave_room(serial)  # Удаляем клиента из комнаты
    clients = room_clients.get(serial, set())
    clients.discard(sid)

    if not clients:
        # Последний клиент ушёл – останавливаем устройство
        conn = active_connections.pop(serial, None)
        if conn:
            logger.info(f"Stopping scrcpy for {serial} (no clients)")
            conn['scrcpy'].scrcpy_stop()
        room_clients.pop(serial, None)
    else:
        logger.debug(f"Client {sid} left, still {len(clients)} clients for {serial}")

@socketio.on('control_data')
def handle_control_data(data):
    """Получены данные управления от клиента – пересылаем на устройство."""
    sid = request.sid
    serial = sid_to_device.get(sid)
    if not serial:
        return
    conn = active_connections.get(serial)
    if conn:
        conn['scrcpy'].scrcpy_send_control(data)

# ---------- Запуск ----------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web scrcpy server')
    parser.add_argument('--outer_port', type=int, required=True, help='Port for web server')
    parser.add_argument('--video_bit_rate', default='512000', help='Video bit rate for scrcpy')
    parser.add_argument('--adb_path', default='adb', help='Path to adb executable')
    parser.add_argument('--scrcpy_server_path', default='web-scrcpy/scrcpy-server.jar', help='Path to scrcpy-server.jar')
    parser.add_argument('--allowed_devices', help='Comma-separated list of allowed serial numbers (optional)')
    cmd_args = parser.parse_args()

    # Присваиваем глобальные переменные из аргументов
    ADB_PATH = cmd_args.adb_path
    SCRCPY_SERVER_PATH = cmd_args.scrcpy_server_path
    if cmd_args.allowed_devices:
        ALLOWED_DEVICES = set(cmd_args.allowed_devices.split(','))

    logger.info(f"Starting server on port {cmd_args.outer_port}")
    socketio.run(app, host='0.0.0.0', port=cmd_args.outer_port, allow_unsafe_werkzeug=True)