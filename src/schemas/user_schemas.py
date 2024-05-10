# src\schemas\user_schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import List

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


class VehicleSchema(BaseModel):
    plate: str
    model: str


class ProfileSchema(BaseModel):
    username: str
    email: EmailStr
    role: Role
    is_blocked: bool
    vehicles: List[VehicleSchema]
