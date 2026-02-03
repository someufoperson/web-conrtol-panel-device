from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

# Пример пользователей с паролями
users = {
    "admin": "password123",  # Имя пользователя: пароль
}

# Функция для проверки имени пользователя и пароля
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route('/')
@auth.login_required
def index():
    return jsonify(message="Вы авторизованы через Basic Authentication!")

if __name__ == '__main__':
    app.run(debug=True)