from db.core.session_maker import async_session
from sqlalchemy import select, update
from db.models.devices import Device, DeviceStatus, BusyStatus
from sqlalchemy.exc import IntegrityError

class DevicesReq:

    @staticmethod
    async def get_all_devices():
        """
        1. Выдать все зарегистрированные устройства (вне зависимости от статуса)
        """
        async with async_session() as session:
            query = (
                select(Device)
            )
            res = await session.execute(query)
            return res.scalars().all()

    @staticmethod
    async def get_device_by_serial_number(serial_number: str):
        """
        2. Выдать одно зарегистрированное устройство по серийному номеру
        """
        async with async_session() as session:
           query = (
               select(Device)
               .where(Device.serial_number == serial_number)
           )
           res = await session.execute(query)
           return res.scalars().one_or_none()


    @staticmethod
    async def edit_status_busy_by_serial_number(serial_number: str, busy_status: BusyStatus):
        """
        3. Изменить статус занятости устройства
        """
        async with async_session() as session:
            await session.execute(
                update(Device)
                .where(Device.serial_number == serial_number)
                .values({"status_busy": busy_status})
            )
            await session.commit()

    @staticmethod
    async def edit_status_online_by_serial_number(serial_number: str, status_online: DeviceStatus):
        """
        4. Изменить статус онлайна устройства
        """
        async with async_session() as session:
            await session.execute(
                update(Device)
                .where(Device.serial_number == serial_number)
                .values({"status_online": status_online})
            )
            await session.commit()

    @staticmethod
    async def create_device(serial_number: str, data: str, local_port: int):
        """
        5. Создание устройства, дописать блок try/except
        """
        async with async_session() as session:
            session.add(Device(serial_number=serial_number,
                               data=data,
                               status_online=DeviceStatus.ONLINE,
                               status_busy=BusyStatus.FREE,
                               local_port=local_port))
            await session.commit()

    @staticmethod
    async def get_all_active_devices():
        """
        6. Вернуть все устройства онлайн зарегистрированные в бд
        """
        async with async_session() as session:
            query = (
                select(Device)
                .where(Device.status_online == DeviceStatus.ONLINE)
            )
            res = await session.execute(query)
            return res.scalars().all()