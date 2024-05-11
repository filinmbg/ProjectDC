# src\schemas\user_schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from src.entity.models import Role


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr
    role: Role

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UpdateProfileSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserVehicle(BaseModel):
    id: int
    plate: str
    brand: str
    model: str
    year: int
    color: str
    body: str
    plate_photo: str
    is_blocked: bool

    class Config:
        from_attributes = True