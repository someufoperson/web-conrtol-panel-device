import random
import string
from db.requests.sessions import SessionReq as sr

def login_generator():
    login = "".join(random.choices(string.ascii_letters, k=10))
    return login

def password_generator():
    password = "".join(random.choices(string.ascii_letters + "!()<>[]", k=16))
    return password

async def inner_port_generator():
    while True:
        port = random.randint(5555, 5655)
        result = await sr.inner_port_exists(port)
        if not result:
            return port

async def outer_port_generator():
    while True:
        port = random.randint(5000, 5100)
        result = await sr.outer_port_exists(port)
        if not result:
            return port