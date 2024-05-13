from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from src.schemas.user_schemas import UserVehicle
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.repository import users
from src.services.role_service import Role, RoleAccess
from src.services.auth_service import auth_service
from src.repository import users as users_repository

access = RoleAccess([Role.admin, Role.user])
access_admin = RoleAccess([Role.admin])

router = APIRouter(prefix='/profile', tags=['User'])


@router.get("/{user_id}/vehicles", response_model=List[UserVehicle], dependencies=[Depends(access)])
async def get_user_vehicles_route(user_id: int, db: AsyncSession = Depends(get_db)):
    vehicles = await users.get_user_vehicles(user_id, db)
    if not vehicles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or has no vehicles")
    return vehicles


@router.delete("/{user_id}", dependencies=[Depends(access_admin)])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):

    deleted = await users_repository.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "User deleted successfully"}


@router.put("/{user_id}", dependencies=[Depends(auth_service.get_current_user)])
async def update_user_name(user_id: int, new_name: str, db: AsyncSession = Depends(get_db)):
    """
    Update user's name by ID.
    """
    updated = await users_repository.update_user_name(db, user_id, new_name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "User name updated successfully"}
