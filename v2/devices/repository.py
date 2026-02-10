import random
from devices.schemas import DeviceCreateSchema, DeviceSchema
from devices.models import Device, DeviceStatus, SessionStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class DeviceRepo:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db


    async def create_device(self, device: DeviceCreateSchema) -> DeviceSchema | dict:
        is_exists = await self.db.execute(select(Device).where(Device.serial_number == device.serial_number)) #TODO: сделать проверку на онлайн
        device_port, flask_port = await self.get_free_ports()

        if is_exists.scalar_one_or_none() is None:
            new_device = Device(**device.model_dump(),
                                    device_port=device_port,
                                    flask_port=flask_port)
            self.db.add(new_device)
            await self.db.commit()
            return DeviceSchema.model_validate(new_device)
        else:
            return {"status": "Устройство уже создано"}


    async def get_all_devices(self) -> list[DeviceSchema]:
        result = await self.db.execute(select(Device))
        return [DeviceSchema.model_validate(x) for x in result.scalars().all()]


    async def get_all_online_devices(self):
        result = await self.db.execute(select(Device.serial_number))
        return [x for x in result.scalars().all()]


    async def get_device_by_serial_number(self, serial_number: str) -> DeviceSchema | None:
        result = await self.db.execute(select(Device).where(Device.serial_number == serial_number))
        return result.scalars().one_or_none()


    async def get_device_by_session_status(self):
        result = await self.db.execute(select(Device)
                                       .where(Device.session_status == SessionStatus.ACTIVE,
                                              Device.pid != None))
        return result.scalars().all()


    async def update_device(self,
                            serial_number: str | None = None,
                            **update_fields) -> DeviceSchema | list[DeviceSchema] | None:
        stmt = update(Device)
        if serial_number:
            stmt = stmt.where(Device.serial_number == serial_number)
        stmt = stmt.values(**update_fields).returning(Device)
        result = await self.db.execute(stmt)
        await self.db.commit()
        if serial_number:
            return result.scalar_one_or_none()
        else:
            row = result.scalars().all()
            return [DeviceSchema.model_validate(x) for x in row]


    async def get_free_ports(self) -> list:
        res = await self.db.execute(select(Device.device_port, Device.flask_port))
        used_port = res.all()
        used_device_port = {row[0] for row in used_port}
        used_flask_port = {row[1] for row in used_port}
        list_free_device_port = list(set(range(5555, 5656)) - used_device_port)
        list_free_flask_port = list(set(range(5000, 5101)) - used_flask_port)
        device_port = random.choice(list_free_device_port)
        flask_port = random.choice(list_free_flask_port)
        return [device_port, flask_port]