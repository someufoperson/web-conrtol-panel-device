from fastapi import APIRouter
from db.models.devices import DeviceStatus, BusyStatus
from pydantic import BaseModel, Field
from db.requests.devices import DevicesReq as dr
from helper.adb_helper import get_devices_from_adb

class DeviceCreateSchema(BaseModel):
    serial_number: str
    data: str

class DeviceSchema(DeviceCreateSchema):
    status_online: DeviceStatus
    status_busy: BusyStatus

router = APIRouter(prefix="/devices", tags=["Устройства"])

@router.get("")
async def get_all_devices() -> list[DeviceSchema]:
    res = await dr.get_all_devices()
    return res

@router.get("/get-all-devices/")
async def get_all_conn_devices() -> None:
    res = get_devices_from_adb()
    return res

@router.post("/create/")
async def create_device(device: DeviceCreateSchema) -> DeviceCreateSchema:
    await dr.create_device(serial_number=device.serial_number, data=device.data)
    device = await dr.get_device_by_serial_number(serial_number=device.serial_number)
    return device

@router.get("/get-all-active-devices/")
async def get_all_active_devices() -> list[DeviceSchema]:
    res = await dr.get_all_active_devices()
    return res

@router.get("/{device_id}/")
async def get_device_by_id(device_id: str) -> DeviceSchema:
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-busy/")
async def update_status_busy_by_id(device_id: str) -> DeviceSchema:
    await dr.edit_status_busy_by_serial_number(serial_number=device_id,
                                               busy_status=BusyStatus.BUSY)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-free/")
async def update_status_free_by_id(device_id: str) -> DeviceSchema:
    await dr.edit_status_busy_by_serial_number(serial_number=device_id,
                                               busy_status=BusyStatus.FREE)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-online/")
async def update_status_online_by_id(device_id: str) -> DeviceSchema:
    await dr.edit_status_online_by_serial_number(serial_number=device_id,
                                                 status_online=DeviceStatus.ONLINE)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res

@router.patch("/{device_id}/status-offline/")
async def update_status_offline_by_id(device_id: str) -> DeviceSchema:
    await dr.edit_status_online_by_serial_number(serial_number=device_id,
                                                 status_online=DeviceStatus.OFFLINE)
    res = await dr.get_device_by_serial_number(serial_number=device_id)
    return res