from uuid import UUID
from db.core.session_maker import async_session
from sqlalchemy import select, update
from db.models.sessions import Session, SessionStatus, ConnectStatus
from datetime import datetime, timedelta

class SessionReq:

    @staticmethod
    async def create_session(device_id: str):
        """
        1. Создание сессии, дописать блок try/except
        """
        async with async_session() as session:
            new_session = Session(device_id=device_id,
                              connect_status=ConnectStatus.DISCONNECTED,
                              session_status=SessionStatus.ACTIVE)
            session.add(new_session)
            await session.commit()
            return new_session.id

    @staticmethod
    async def update_session_active_by_session_id(session_id: str, status: SessionStatus):
        """
        2. Изменить статус сессии (деактивация)
        """
        session_id = UUID(session_id)
        async with async_session() as session:
            await session.execute(
                update(Session)
                .where(Session.id == session_id)
                .values({"session_status": status})
            )
            await session.commit()

    @staticmethod
    async def update_session_connect_by_session_id(session_id: str, status: ConnectStatus):
        """
        3. Изменить статус подключения к сессии
        """
        session_id = UUID(session_id)
        async with async_session() as session:
            await session.execute(
                update(Session)
                .where(Session.id == session_id)
                .values({"connect_status": status})
            )
            await session.commit()

    @staticmethod
    async def get_all_sessions():
        """
        4. Выдать все активные сессии
        """
        async with async_session() as session:
            query = (
                select(Session)
                .where(Session.session_status == SessionStatus.ACTIVE)
            )
            res = await session.execute(query)
            return res.scalars().all()

    @staticmethod
    async def get_session_by_id(session_id: str):
        """
        5. Выдать одну активную сессию по id
        """
        session_id = UUID(session_id)
        async with async_session() as session:
            query = (
                select(Session)
                .where(Session.id == session_id)
            )
            res = await session.execute(query)
            return res.scalars().one_or_none()