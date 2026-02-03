import uvicorn
from db.core.init_db import create_meta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from api.routers import all_routers

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in all_routers:
    app.include_router(router)


if __name__ == "__main__":
    asyncio.run(create_meta())
    uvicorn.run(app="main:app", reload=True)