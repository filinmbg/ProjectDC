import cloudinary
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import db
from src.entity.models import Vehicle
from src.schemas.vehicles_schemas import VehicleCreate
from src.conf.config import config
from src.repository.vehicles import upload_to_cloudinary, car_info_response


cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET
)

router = APIRouter(tags=['Vehicle'])


# @router.post("/vehicles/")
# async def create_vehicle(image: UploadFile = File(...)):
#     try:
#         contents = await image.read()
#         cloudinary_response = upload_to_cloudinary(contents)
#         plate_info = await car_info_response(cloudinary_response['url'])
#         if plate_info is None:
#             raise HTTPException(status_code=404, detail="Plate information not found")
#
#         vehicle_data = VehicleCreate(
#             plate=plate_info['plate'],
#             brand=plate_info['brand'],
#             model=plate_info['model'],
#             year=int(plate_info['year']),
#             color=plate_info['color'],
#             body=plate_info['body'],
#             plate_photo=cloudinary_response['url'],
#         )
#         print(vehicle_data)
#         async with db() as session:
#             try:
#                 session.add(vehicle_data)
#                 await session.commit()
#                 await session.refresh(vehicle_data)
#             except Exception as e:
#                 await session.rollback()
#                 raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
#             finally:
#                 await session.close()
#
#         return {
#             "message": "Vehicle created successfully"
#         }
#     except HTTPException as he:
#         raise he
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
@router.post("/vehicles/")
async def create_vehicle(image: UploadFile = File(...)):
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
        )
        return {
            "message": "Vehicle created successfully",
            "vehicle_data": vehicle_data
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
