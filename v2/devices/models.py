import datetime
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from core.database import Base


class DeviceStatus(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class SessionStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ConnectionStatus(Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class Device(Base):
    __tablename__ = 'devices'

    serial_number: Mapped[str] = mapped_column(String(length=128), primary_key=True)
    label: Mapped[str] = mapped_column(String(length=128), nullable=True)
    status_device: Mapped[DeviceStatus] = mapped_column(default=DeviceStatus.ONLINE)
    session_status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.INACTIVE)
    connection_status: Mapped[ConnectionStatus] = mapped_column(default=ConnectionStatus.DISCONNECTED)
    device_port: Mapped[int] = mapped_column(unique=True)
    flask_port: Mapped[int] = mapped_column(unique=True)
    pid: Mapped[int] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),
                                                          onupdate=datetime.datetime.utcnow)