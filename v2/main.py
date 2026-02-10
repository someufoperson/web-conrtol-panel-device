from fastapi import FastAPI
from core import subprocess_helper as sub
from core.database import create_meta, nullable_table
from devices.api import router as devices_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

app = FastAPI(docs_url="/")

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

async def main():
    await create_meta()
    await nullable_table()
    sub.start_redis_docker()
    sub.status_online_helper()

app.include_router(devices_router)

if __name__ == "__main__":
    asyncio.run(main())
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")