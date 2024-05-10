from typing import Optional
from pydantic import BaseModel


class VehicleCreate(BaseModel):
    plate: str
    brand: str
    model: str
    year: int
    color: str
    body: str
    plate_photo: Optional[str] = None
    is_blocked: Optional[bool] = False
    owner_id: int
