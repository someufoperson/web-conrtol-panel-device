from flask import Flask, render_template, request
from flask_httpauth import HTTPBasicAuth
from flask_socketio import SocketIO, emit, send
from scrcpy import Scrcpy
import argparse
import queue
import requests
from loguru import logger
import sys

logger.remove()
logger.add("sessions.log", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(sys.stdout, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

scpy_ctx = None
client_sid = None
message_queue = queue.Queue()
video_bit_rate = "1024000"

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=None)

def create_route(link: str, title: str, serv_login: str, serv_password: str):

    @auth.verify_password
    def verify_password(username, password):
        if username == serv_login and password == serv_password:
            return username

    @app.route(f'/{link}')
    @auth.login_required
    def index():
        return render_template('index.html', title=title)

    @app.route(f'/{link}/check-health')
    def check_health():
        return {"status": "ok"}

def video_send_task():
    global client_sid
    while client_sid != None:
        try:
            message = message_queue.get(timeout=0.01)
            socketio.emit('video_data', message, to=client_sid)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error sending data: {e}")
        finally:
            socketio.sleep(0.001)
    print(f"video_send_task stopped")

def send_video_data(data):
    message_queue.put(data)


@socketio.on('connect')
def handle_connect():
    global scpy_ctx, client_sid

    requests.patch(f"http://127.0.0.1:8000/sessions/{args.link}/connect/")
    if scpy_ctx is not None:
        return False
    else:
        client_sid = request.sid
        logger.info(f"Подключился пользователь с IP: {request.remote_addr}, SESSION_ID:{args.link}")
        scpy_ctx = Scrcpy(serial_number=args.serial_number, local_port=int(args.port))
        scpy_ctx.scrcpy_start(send_video_data, video_bit_rate)
        socketio.start_background_task(video_send_task)

@socketio.on('disconnect')
def handle_disconnect():
    requests.patch(f"http://127.0.0.1:8000/sessions/{args.link}/disconnect/")
    logger.info(f"Отключился пользователь с IP: {request.remote_addr}, SESSION_ID:{args.link}")
    global scpy_ctx, client_sid
    client_sid = None
    scpy_ctx.scrcpy_stop()
    scpy_ctx = None

@socketio.on('control_data')
def handle_control_data(data):
    global scpy_ctx
    scpy_ctx.scrcpy_send_control(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Web server')
    parser.add_argument('--video_bit_rate', default="1024000", help='scrcpy video bit rate')
    parser.add_argument('--serial_number')
    parser.add_argument('--port')
    parser.add_argument('--link')
    parser.add_argument('--outer_port')
    parser.add_argument('--title')
    parser.add_argument('--login')
    parser.add_argument('--password')
    args = parser.parse_args()
    create_route(args.link, args.title, args.login, args.password)
    outer_port = args.outer_port
    video_bit_rate = args.video_bit_rate
    socketio.run(app, host='0.0.0.0', port=int(outer_port), allow_unsafe_werkzeug=True)