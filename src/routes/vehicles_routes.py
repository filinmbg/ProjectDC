import cloudinary
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.entity.models import Vehicle, User
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
async def create_vehicle(image: UploadFile = File(), owner_id: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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


