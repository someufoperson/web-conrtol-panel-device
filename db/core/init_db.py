from db.core.base import Base
from db.core.session_maker import engine

async def create_meta():
    async with engine.begin() as conn:
        from db.models.sessions import Session
        from db.models.devices import Device
        await conn.run_sync(Base.metadata.drop_all) #на случай тестов (дропает бд чтобы не удалять)
        await conn.run_sync(Base.metadata.create_all)