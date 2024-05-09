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
    address = Column(String(255))
    phone_number = Column(String(15))
    email = Column(EmailType, unique=True, index=True)
    role = Column("role", Enum(Role), default=Role.user)
    is_blocked = Column(Boolean, default=False)


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

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id = Column(Integer, primary_key=True, index=True)
    spot_number = Column(String(10), unique=True, index=True)
    status = Column(String(20), default="free")
    spot_type = Column(String(20))


class MovementLog(Base):
    __tablename__ = "movement_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    entry_time = Column(DateTime, default=func.now())
    exit_time = Column(DateTime, nullable=True)
    parking_spot_id = Column(Integer, ForeignKey("parking_spots.id"), nullable=True)
    status = Column(String(10))


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    payment_datetime = Column(DateTime, default=func.now())


User.vehicles = relationship("Vehicle", back_populates="owner")
User.payments = relationship("Payment", back_populates="user")
Vehicle.owner = relationship("User", back_populates="vehicles")
ParkingSpot.logs = relationship("MovementLog", back_populates="parking_spot")
User.logs = relationship("MovementLog", back_populates="user")