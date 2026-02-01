from db.core.base import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

class DeviceStatus(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"

class BusyStatus(Enum):
    BUSY = "BUSY"
    FREE = "FREE"

class Device(Base):
    __tablename__ = "devices"

    serial_number: Mapped[str] = mapped_column(String(length=128), primary_key=True)
    data: Mapped[str] = mapped_column(String(length=128))
    status_online: Mapped[DeviceStatus] = mapped_column(default=DeviceStatus.OFFLINE)
    status_busy: Mapped[BusyStatus] = mapped_column(default=BusyStatus.FREE)
    local_port: Mapped[int] = mapped_column(unique=True)