from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import update
from core.config import db_settings

engine = create_async_engine(url=db_settings.DB_URL, echo=db_settings.ECHO)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    def __repr__(self):
        cols = []
        for col in self.__table__.columns.keys():
            cols.append(f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__}({', '.join(cols)})>"


async def nullable_table():
    async with async_session() as session:
        from devices.models import Device, SessionStatus, ConnectionStatus
        await session.execute(update(Device).values({"session_status": SessionStatus.INACTIVE,
                                                     "connection_status": ConnectionStatus.DISCONNECTED,
                                                     "pid": None}))
        await session.commit()


async def create_meta() -> None:
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) #for testing db
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session():
    async with async_session() as session:
        yield session