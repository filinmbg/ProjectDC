from pydantic import BaseModel, EmailStr, Field

from src.entity.models import Role


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    password: str
    address: str
    phone_number: str
    email: EmailStr
    role: Role
    is_blocked: bool

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"