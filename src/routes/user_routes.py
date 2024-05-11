from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from src.schemas.user_schemas import UserVehicle
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.repository import users

router = APIRouter(prefix='/profile', tags=['User'])


@router.get("/{user_id}/vehicles", response_model=List[UserVehicle])
async def get_user_vehicles_route(user_id: int, db: AsyncSession = Depends(get_db)):
    vehicles = await users.get_user_vehicles(user_id, db)
    if not vehicles:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or has no vehicles")
    return vehicles
