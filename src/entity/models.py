from sqlalchemy import Column, Integer, String, Boolean, func, Table, Enum
import enum

from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

Base = declarative_base()

image_m2m_tag = Table(
    "image_m2m_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("image_id", Integer, ForeignKey("images.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)


class Role(enum.Enum):
    __tablename__ = "users_roles"
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(45), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    avatar = Column(String(255), nullable=False)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, default=func.now(), onupdate=func.now())
    refresh_token = Column(String(255))
    forbidden = Column(Boolean, default=False)
    role = Column("role", Enum(Role), default=Role.user)
    images = relationship("Image", backref="users")
    user_image = Column(String(255), nullable=True)


