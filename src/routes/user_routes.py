from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth_service import auth_service
from src.schemas.user_schemas import UserResponse

router = APIRouter(prefix='/user', tags=['User'])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: UserResponse = Depends(auth_service.get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """
    Get user profile.
    """
    return current_user
