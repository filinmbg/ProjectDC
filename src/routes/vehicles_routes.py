import cloudinary
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends

from fastapi.responses import FileResponse
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.payments import calculate_parking_cost, calculate_parking_duration, \
    calculate_total_parking_duration, convert_seconds_to_time, generate_payment_report, generate_payment_report_for_vehicle, record_entry_exit_time
from src.database.db import get_db
from src.entity.models import MovementLog, Vehicle, User
from src.schemas.vehicles_schemas import VehicleCreate
from src.conf.config import config
from src.repository.vehicles import upload_to_cloudinary, car_info_response, get_vehicle_info_by_plate
from src.services.auth_service import get_current_user
from src.services.role_service import Role, RoleAccess

admin_access = RoleAccess([Role.admin])


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
        if owner_id.role != Role.admin:
            raise HTTPException(status_code=403, detail="Forbidden, you do not have administrator rights")

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


@router.post("/entry-exit/", status_code=201, dependencies=[Depends(admin_access)])
async def record_entry_exit(vehicle_id: int, entry: bool, session: AsyncSession = Depends(get_db)):
    try:
        vehicle = await session.get(Vehicle, vehicle_id)  # Отримання об'єкта Vehicle по id
        user_id = vehicle.owner_id  # Отримання owner_id з об'єкта Vehicle
        await record_entry_exit_time(session, vehicle_id, entry, user_id)
        return {"message": "Entry/exit time recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parking-duration/", status_code=201, dependencies=[Depends(admin_access)])
async def calculate_parking_duration_route(movement_log_id: int, session: AsyncSession = Depends(get_db)):
    try:
        duration = await calculate_parking_duration(session, movement_log_id)
        total_seconds = duration.total_seconds()
        return await convert_seconds_to_time(int(total_seconds))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-parking-cost/{movement_log_id}", status_code=201, dependencies=[Depends(admin_access)])
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


@router.post("/calculate-total-parking-duration/{vehicle_id}", status_code=201, dependencies=[Depends(admin_access)])
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



@router.get("/payment/report", status_code=201, dependencies=[Depends(admin_access)])
async def export_payment_report(session: AsyncSession = Depends(get_db)):
    try:
        # Викликаємо функцію генерації звіту про розрахунки
        report_file_name = await generate_payment_report(session)

        # Перевіряємо, чи був успішно створений звіт
        if report_file_name:
            return FileResponse(report_file_name, filename=report_file_name, media_type='text/csv')
        else:
            raise HTTPException(
                status_code=500, detail="Failed to generate payment report")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment/report/{vehicle_id}", status_code=201, dependencies=[Depends(admin_access)])
async def export_payment_report_for_vehicle(vehicle_id: int, session: AsyncSession = Depends(get_db)):
    try:
        # Викликаємо функцію генерації звіту про розрахунки для конкретного автомобіля
        report_file_name = await generate_payment_report_for_vehicle(session, vehicle_id)

        # Перевіряємо, чи був успішно створений звіт
        if report_file_name:
            return FileResponse(report_file_name, filename=report_file_name, media_type='text/csv')
        else:
            raise HTTPException(
                status_code=500, detail="Failed to generate payment report for vehicle")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vehicles/{plate}", response_model=dict, status_code=201, dependencies=[Depends(admin_access)])
async def get_vehicle_info_route(plate: str, session: AsyncSession = Depends(get_db)):
    vehicle_info = await get_vehicle_info_by_plate(plate, session)
    if "error" in vehicle_info:
        raise HTTPException(status_code=404, detail=vehicle_info["error"])
    return vehicle_info
