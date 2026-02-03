import uuid
from db.core.base import Base
from sqlalchemy import Uuid, ForeignKey, text, func
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
import datetime
from helper import data_gen

class ConnectStatus(Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"

class SessionStatus(Enum):
    EXPIRED = "EXPIRED"
    ACTIVE = "ACTIVE"


class Session(Base):
    __tablename__ = 'sessions'

    id: Mapped[uuid.UUID] = mapped_column(Uuid,
                                          primary_key=True,
                                          default=lambda: uuid.uuid4())
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.serial_number", ondelete="CASCADE"), nullable=False)
    connect_status: Mapped[ConnectStatus] = mapped_column(default=ConnectStatus.DISCONNECTED)
    session_status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.ACTIVE)
    inner_port: Mapped[int]
    outer_port: Mapped[int]
    login: Mapped[str] = mapped_column(default=lambda: data_gen.login_generator())
    password: Mapped[str] = mapped_column(default=lambda: data_gen.password_generator())
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(),
                                                          onupdate=datetime.datetime.utcnow)