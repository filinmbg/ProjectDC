import enum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy_utils import EmailType

Base = declarative_base()


class Role(enum.Enum):
    admin = "admin"
    guest = "guest"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    email = Column(EmailType, unique=True, index=True)
    role = Column("role", Enum(Role), default=Role.user)
    is_blocked = Column(Boolean, default=False)

    vehicles = relationship("Vehicle", back_populates="owner")
    payments = relationship("Payment", back_populates="user")
    logs = relationship("MovementLog", back_populates="user")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(20), unique=True, index=True)
    brand = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    color = Column(String(50))
    body = Column(String(50))
    plate_photo = Column(String(255), nullable=True)
    is_blocked = Column(Boolean, default=False)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="vehicles")

    logs = relationship("MovementLog", back_populates="vehicle")

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id = Column(Integer, primary_key=True, index=True)
    spot_number = Column(String(10), unique=True, index=True)
    status = Column(String(20), default="free")
    spot_type = Column(String(20))

    logs = relationship("MovementLog", back_populates="parking_spot")


class MovementLog(Base):
    __tablename__ = "movement_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    entry_time = Column(DateTime, default=func.now())
    exit_time = Column(DateTime, nullable=True)
    parking_spot_id = Column(Integer, ForeignKey("parking_spots.id"), nullable=True)
    status = Column(String(10))

    user = relationship("User", back_populates="logs")
    vehicle = relationship("Vehicle", back_populates="logs")
    parking_spot = relationship("ParkingSpot", back_populates="logs")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cost_per_hour = Column(Integer)
    amount = Column(Integer)
    payment_datetime = Column("payment_datetime", DateTime, default=func.now())

    user = relationship("User", back_populates="payments")