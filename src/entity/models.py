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
    guest: str = "guest"
    user: str = "user"


class User(Base):
    __tablename__ = "users"
    id_user = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(45), nullable=False, unique=True)
    phonenumber = Column(String(12), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    forbidden = Column(Boolean, default=False)
    role = Column("role", Enum(Role), default=Role.user)
    id_car = Column(String(12), nullable=False, unique=True)

class Vehicles(Base):
    __tablename__ = "users"
    id_car = Column(Integer, primary_key=True)
    licenseplate = Column(Integer, primary_key=True)
    model = Column(String(50), nullable=False, unique=True)
    year = Column(String(4), nullable=False, unique=True)
    id_user = Column(String(20), nullable=True, unique=True)
    blocked = Column(Boolean, default=False)

class Parking(Base):
    id_parking = Column(Integer, primary_key=True)
    numbers = Column(String(10), unique=True)

class Registration(Base):
    id_regist = Column(Integer, primary_key=True)