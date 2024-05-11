from typing import List
import cloudinary
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.payments import calculate_parking_cost, calculate_parking_duration, \
    calculate_total_parking_duration, record_entry_exit_time
from src.database.db import get_db
from src.entity.models import MovementLog, Vehicle, User
from src.schemas.vehicles_schemas import VehicleCreate
from src.conf.config import config
from src.repository.vehicles import upload_to_cloudinary, car_info_response
from src.services.auth_service import get_current_user

cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET
)

router = APIRouter(tags=['Vehicle'])


@router.post("/vehicles/")
async def create_vehicle(image: UploadFile = File(), owner_id: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    try:
        contents = await image.read()
        cloudinary_response = upload_to_cloudinary(contents)
        plate_info = await car_info_response(cloudinary_response['url'])
        if plate_info is None:
            raise HTTPException(status_code=404, detail="Plate information not found")
        vehicle_data = VehicleCreate(
            plate=plate_info['plate'],
            brand=plate_info['brand'],
            model=plate_info['model'],
            year=int(plate_info['year']),
            color=plate_info['color'],
            body=plate_info['body'],
            plate_photo=cloudinary_response['url'],
            owner_id=owner_id.id
        )
        vehicle = Vehicle(**vehicle_data.dict())
        db.add(vehicle)
        await db.commit()
        await db.refresh(vehicle)
        return {
            "message": "Vehicle created successfully",
            "vehicle_data": vehicle
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/entry-exit/")
async def record_entry_exit(vehicle_id: int, entry: bool, session: AsyncSession = Depends(get_db)):
    try:
        vehicle = await session.get(Vehicle, vehicle_id)  # Отримання об'єкта Vehicle по id
        user_id = vehicle.owner_id  # Отримання owner_id з об'єкта Vehicle
        await record_entry_exit_time(session, vehicle_id, entry, user_id)
        return {"message": "Entry/exit time recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parking-duration/")
async def calculate_parking_duration_route(movement_log_id: int, session: AsyncSession = Depends(get_db)):
    try:
        duration = await calculate_parking_duration(session, movement_log_id)
        return {"parking_duration_seconds": duration.total_seconds()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-parking-cost/{movement_log_id}")
async def calculate_parking_cost_route(movement_log_id: int, cost_per_hour: int,
                                       session: AsyncSession = Depends(get_db)):
    try:
        cost = await calculate_parking_cost(session, movement_log_id, cost_per_hour)
        if cost is not None:
            return {"cost": cost}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to calculate parking cost")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-total-parking-duration/{vehicle_id}")
async def calculate_total_parking_duration_route(vehicle_id: int, session: AsyncSession = Depends(get_db)):
    try:
        total_duration = await calculate_total_parking_duration(session, vehicle_id)
        if total_duration is not None:
            return {"total_duration": total_duration}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to calculate total parking duration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
