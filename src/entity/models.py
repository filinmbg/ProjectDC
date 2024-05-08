from sqlalchemy import Column, Integer, String, Boolean, func, Table, Enum
import enum
from django.db import models
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




class User(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()


class Vehicle(models.Model):
    plate = models.CharField(max_length=20)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    color = models.CharField(max_length=50)
    body = models.CharField(max_length=50)
    plate_photo = models.ImageField(upload_to='plate_photos/', null=True, blank=True)

    owner = models.ForeignKey('User', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

class ParkingSpot(models.Model):
    id = models.AutoField(primary_key=True)
    spot_number = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=[('free', 'Вільне'), ('occupied', 'Зайняте')])
    spot_type = models.CharField(max_length=20)

class MovementLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[("entry", "В'їзд"), ("exit", "Виїзд")])

class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_datetime = models.DateTimeField()