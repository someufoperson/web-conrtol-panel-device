import asyncio
import random
from uuid import UUID
from db.core.session_maker import async_session, sync_session
from sqlalchemy import select, update
from db.models.sessions import Session, SessionStatus, ConnectStatus
from datetime import datetime, timedelta

class SessionReq:

    @staticmethod
    async def create_session(device_id: str, inner_port: int, outer_port: int):
        """
        1. Создание сессии, дописать блок try/except
        """
        async with async_session() as session:
            new_session = Session(device_id=device_id,
                                  connect_status=ConnectStatus.DISCONNECTED,
                                  session_status=SessionStatus.ACTIVE,
                                  inner_port=inner_port,
                                  outer_port=outer_port)
            session.add(new_session)
            await session.commit()
            return new_session

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

    @staticmethod
    async def inner_port_exists(port: int):
        """
        6. Проверка на существование текущей сессии с интересующим портом
        """
        async with async_session() as session:
            query = (
                select(Session.inner_port)
                .where(Session.inner_port == port and Session.session_status == SessionStatus.ACTIVE)
            )
            res = await session.execute(query)
            return res.scalars().one_or_none()

    @staticmethod
    async def outer_port_exists(port: int):
        """
        7. Проверка на существование текущей сессии с интересующим портом
        """
        async with async_session() as session:
            query = (
                select(Session.outer_port)
                .where(Session.outer_port == port and Session.session_status == SessionStatus.ACTIVE)
            )
            res = await session.execute(query)
            return res.scalars().one_or_none()

    @staticmethod
    async def insert_pid(session_id: str, pid: int):
        """
        8. Добавление pid процесса сервера, для дальнейшего disconnect
        """
        # session_id = UUID(session_id)
        async with async_session() as session:
            await session.execute(
                update(Session)
                .where(Session.id == session_id)
                .values({"pid": pid})
            )
            await session.commit()