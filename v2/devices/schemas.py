from pydantic import BaseModel, Field
from devices.models import DeviceStatus, SessionStatus, ConnectionStatus

class DeviceCreateSchema(BaseModel):
    serial_number: str = Field(..., max_length=128)
    label: str = Field(max_length=128)

    class Config:
        from_attributes = True

class DeviceSchema(DeviceCreateSchema):
    status_device: DeviceStatus
    connection_status: ConnectionStatus
    session_status: SessionStatus
    device_port: int = Field(ge=5555, le=5655)
    flask_port: int = Field(ge=5000, le=5100)
    pid: int | None

    class Config:
        from_attributes = True

class DeviceSerialNumberSchema(BaseModel):
    serial_number: str = Field(..., max_length=128)