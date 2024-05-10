from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth_service import auth_service
from src.schemas.user_schemas import UserResponse, ProfileSchema, VehicleSchema
from src.repository import users as repository_users

router = APIRouter(prefix='/user', tags=['User'])


@router.get("/profile", response_model=ProfileSchema)
async def get_user_profile(current_user: ProfileSchema = Depends(auth_service.get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """
    Get user profile.
    """
    user = await repository_users.get_user_by_email(current_user.email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    vehicles = [VehicleSchema(plate=vehicle.plate, model=vehicle.model) for vehicle in user.vehicles]

    return ProfileSchema(username=current_user.username, email=current_user.email, role=current_user.role,
                         is_blocked=current_user.is_blocked, vehicles=vehicles)