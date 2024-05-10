from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class VehicleCreate(BaseModel):
    plate: str
    brand: str
    model: str
    year: int
    color: str
    body: str
    plate_photo: Optional[str] = None
    is_blocked: Optional[bool] = False


class ParkingRecord(BaseModel):
    user_id: int
    license_plate: str
    entry_time: datetime
    exit_time: datetime
    total_cost: float
    notified: bool = False
