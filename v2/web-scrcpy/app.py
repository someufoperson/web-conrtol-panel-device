from flask import Flask, render_template, request
from flask_httpauth import HTTPBasicAuth
from flask_socketio import SocketIO, emit, disconnect
from scrcpy import Scrcpy
import argparse
import queue
import requests
from loguru import logger
import sys
import time
import threading

#TODO: запись видео в папочку

logger.remove()
logger.add("sessions.log", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(sys.stdout, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

scpy_ctx = None
client_sid = None
message_queue = queue.Queue()
video_bit_rate = "1024000"

inactivity_timer = None

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, async_mode=None, ping_timeout=180, ping_interval=30)


def create_route(serial_number: str, title: str):
    @app.route(f'/{serial_number}')
    def index():
        return render_template('index.html', title=title)

    @app.route(f'/{serial_number}/check-health')
    def check_health():
        return {"status": "ok"}


def video_send_task():
    global client_sid
    while client_sid is not None:
        try:
            message = message_queue.get(timeout=0.01)
            socketio.emit('video_data', message, to=client_sid)
        except queue.Empty:
            pass
        finally:
            time.sleep(0.001)


def send_video_data(data):
    try:
        message_queue.put(data, timeout=0.01)
    except queue.Full:
        pass


def disconnect_due_to_inactivity():
    global client_sid, scpy_ctx, inactivity_timer
    if client_sid:
        if scpy_ctx:
            scpy_ctx.scrcpy_stop()
            scpy_ctx = None
        requests.patch(f"http://127.0.0.1:8000/v1/devices/update-status/connect/{args.serial_number}/disconnect/")
        disconnect(client_sid)
        client_sid = None
    inactivity_timer = None


def reset_inactivity_timer():
    global inactivity_timer
    if inactivity_timer:
        inactivity_timer.cancel()
    inactivity_timer = threading.Timer(180.0, disconnect_due_to_inactivity)
    inactivity_timer.daemon = True
    inactivity_timer.start()


@socketio.on('connect')
def handle_connect():
    global scpy_ctx, client_sid
    if scpy_ctx is not None:
        return False
    requests.patch(f"http://127.0.0.1:8000/v1/devices/update-status/connect/{args.serial_number}/connect")
    client_sid = request.sid
    logger.info(
        f"Подключился пользователь с IP: {request.remote_addr}, SESSION_ID:{args.serial_number}")
    while not message_queue.empty():
        try:
            message_queue.get_nowait()
        except:
            break
    try:
        scpy_ctx = Scrcpy(serial_number=args.serial_number, local_port=int(args.port))
        scpy_ctx.scrcpy_start(send_video_data, video_bit_rate)
    except Exception as e:
        logger.error(f"Ошибка запуска scrcpy: {e}")
        emit('error', {'message': 'Failed to start video stream'})
        return False
    socketio.start_background_task(video_send_task)
    reset_inactivity_timer()
    return True


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    global scpy_ctx, client_sid, inactivity_timer
    if sid == client_sid:
        if inactivity_timer:
            inactivity_timer.cancel()
            inactivity_timer = None
        if scpy_ctx:
            try:
                scpy_ctx.scrcpy_stop()
            except:
                pass
            scpy_ctx = None
        client_sid = None
        logger.info(
            f"Отключился пользователь с IP: {request.remote_addr}, SESSION_ID:{args.serial_number}")
        requests.patch(f"http://127.0.0.1:8000/v1/devices/update-status/connect/{args.serial_number}/disconnect/")


@socketio.on('control_data')
def handle_control_data(data):
    global scpy_ctx, client_sid
    sid = request.sid
    if sid != client_sid:
        return
    reset_inactivity_timer()
    if scpy_ctx:
        scpy_ctx.scrcpy_send_control(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web server')
    parser.add_argument('--video_bit_rate', default="1024000", help='scrcpy video bit rate')
    parser.add_argument('--serial_number')
    parser.add_argument('--port')
    parser.add_argument('--outer_port')
    parser.add_argument('--title')
    args = parser.parse_args()
    create_route(args.serial_number, args.title)
    outer_port = args.outer_port
    video_bit_rate = args.video_bit_rate
    socketio.run(app, host='0.0.0.0', port=int(outer_port), allow_unsafe_werkzeug=True)