from threading import Thread
import subprocess
import socket
import time

class Scrcpy:
    def __init__(self, serial_number: str, local_port: int, adb_path: str, server_path: str):
        self.video_socket = None
        self.audio_socket = None
        self.control_socket = None

        self.android_thread = None
        self.video_thread = None
        self.audio_thread = None
        self.control_thread = None
        self.android_process = None

        self.serial_number = serial_number
        self.local_port = local_port
        self.adb_path = adb_path
        self.server_path = server_path
        self.stop = False

    def push_server_to_device(self):
        device_server_path = "/data/local/tmp/scrcpy-server.jar"
        result = subprocess.run(
            [self.adb_path, "-s", self.serial_number, "push", r"C:\Users\myapo\Documents\Python\PythonProject\ADB_control_panel\v3\test_scrcpy\web-scrcpy\scrcpy-server", device_server_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error pushing server: {result.stderr}")
            return False
        return True

    def setup_adb_forward(self):
        subprocess.run(
            [self.adb_path, "-s", self.serial_number, "forward", f"tcp:{self.local_port}", "localabstract:scrcpy"],
            check=True
        )

    def remove_adb_forward(self):
        subprocess.run(
            [self.adb_path, "-s", self.serial_number, "forward", "--remove", f"tcp:{self.local_port}"],
            capture_output=True
        )

    def start_server(self):
        device_server_path = "/data/local/tmp/scrcpy-server.jar"
        cmd = [
            self.adb_path, "-s", self.serial_number, "shell",
            f"CLASSPATH={device_server_path} app_process / com.genymobile.scrcpy.Server 3.1 "
            f"tunnel_forward=true log_level=VERBOSE video_bit_rate={self.video_bit_rate}"
        ]
        self.android_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while not self.stop:
            stderr_line = self.android_process.stderr.readline().decode().strip()
            if not stderr_line:
                break
            if stderr_line:
                print(f"Server error: {stderr_line}")
        self.android_process.wait()
        print("Server stopped")

    def receive_video_data(self):
        print("Receiving video data (H.264)...")
        # пропускаем первый байт (dummy)
        self.video_socket.recv(1)
        while not self.stop:
            try:
                data = self.video_socket.recv(262144)  # 256 КБ
                if not data:
                    break
                self.video_callback(data)
            except socket.error:
                break
        print("Video data reception stopped")

    def receive_audio_data(self):
        print("Receiving audio data...")
        self.audio_socket.recv(1)
        while not self.stop:
            data = self.audio_socket.recv(1024)
            if not data:
                break
        print("Audio data reception stopped")

    def handle_control_conn(self):
        print("Control connection established (idle)...")
        self.control_socket.recv(1)
        while not self.stop:
            data = self.control_socket.recv(1024)
            if not data:
                break
            # Обработка входящих управляющих сообщений (от устройства) – пока игнорируем
        print("Control connection stopped")

    def scrcpy_start(self, video_callback, video_bit_rate):
        self.video_bit_rate = video_bit_rate
        self.video_callback = video_callback
        self.stop = False

        if not self.push_server_to_device():
            print("Failed to push server files to device.")
            return

        self.setup_adb_forward()
        self.android_thread = Thread(target=self.start_server, daemon=True)
        self.android_thread.start()
        time.sleep(2)

        # video connection
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket.connect(('localhost', self.local_port))
        print("Video connection established")

        # audio connection
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket.connect(('localhost', self.local_port))
        print("Audio connection established")

        # control connection
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_socket.connect(('localhost', self.local_port))
        print("Control connection established")

        self.video_thread = Thread(target=self.receive_video_data, daemon=True)
        self.audio_thread = Thread(target=self.receive_audio_data, daemon=True)
        self.control_thread = Thread(target=self.handle_control_conn, daemon=True)
        self.video_thread.start()
        self.audio_thread.start()
        self.control_thread.start()
        print("Background tasks started")

    def scrcpy_stop(self):
        print("Stopping Scrcpy")
        self.stop = True
        # закрываем сокеты для выхода из циклов
        if self.video_socket:
            self.video_socket.shutdown(socket.SHUT_RDWR)
            self.video_socket.close()
        if self.audio_socket:
            self.audio_socket.close()
        if self.control_socket:
            self.control_socket.shutdown(socket.SHUT_RDWR)
            self.control_socket.close()

        if self.video_thread:
            self.video_thread.join()
        if self.audio_thread:
            self.audio_thread.join()
        if self.control_thread:
            self.control_thread.join()

        if self.android_process:
            self.android_process.terminate()
        if self.android_thread:
            self.android_thread.join()

        self.remove_adb_forward()
        print("Scrcpy stopped")

    def scrcpy_send_control(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.control_socket.send(data)