from typing import Any

from pydantic import ConfigDict, field_validator, EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/Parking"
    SECRET_KEY_JWT: str = "1234567890"
    ALGORITHM: str = "HS256"
    MAIL_USERNAME: EmailStr = "postgres@meail.com"
    MAIL_PASSWORD: str = "postgres"
    MAIL_FROM: str = "postgres"
    MAIL_PORT: int = 567234
    MAIL_SERVER: str = "postgres"
    # REDIS_DOMAIN: str = 'localhost'
    # REDIS_PORT: int = 6379
    # REDIS_PASSWORD: str | None = None
    # CLD_NAME: str = 'photoshare'
    # CLD_API_KEY: int = 326488457974591
    # CLD_API_SECRET: str = "secret"
    CLOUDINARY_NAME: str = "dknkinnlb"
    CLOUDINARY_API_KEY: int = 763413813135315
    CLOUDINARY_API_SECRET: str = "yhMztWViP9KNz7uH71tF2zgTQ_I"
    BGCARS_API_KEY: str = "08330252d37dcc578f5881cf3662ea90"

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: Any):
        if v not in ["HS256", "HS512"]:
            raise ValueError("algorithm must be HS256 or HS512")
        return v

    model_config = ConfigDict(extra='ignore', env_file=".env", env_file_encoding="utf-8")  # noqa


config = Settings()
