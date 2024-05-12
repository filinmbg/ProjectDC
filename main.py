from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse, JSONResponse

from Project_DC.src.schemas.vehicles_schemas import ParkingRecord
from src import schemas
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.routes import auth_routes, vehicles_routes
import time
from datetime import datetime
import pathlib


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware('http')
async def custom_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    during = time.time() - start_time
    response.headers['performance'] = str(during)
    return response


BASE_DIR = pathlib.Path(__file__).parent
# app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory='templates')


# @app.get("/", response_class=HTMLResponse, description="Project DC", tags=["Main index.html"])
# async def root(request: Request):
#     return templates.TemplateResponse('index.html', {"request": request, "title": "Project DC"})


@app.get("/api/healthchecker", tags=["Tools"])
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


app.include_router(auth_routes.router, prefix="/api")
app.include_router(vehicles_routes.router)

@app.post("/parking_record/")
async def add_parking_record(record: ParkingRecord, parking_records=None):
    parking_records.append(record)
    if record.total_cost > 5 and not record.notified:
        record.notified = True
    return {"message": "Parking record added successfully"}

@app.get("/generate_report/")
async def generate_report():
    report_data = "\n".join([f"{record.user_id},{record.license_plate},{record.entry_time},{record.exit_time},{record.total_cost}" for record in parking_records])
    file_name = "parking_report.csv"
    with open(file_name, "w") as f:
        f.write("User ID,License Plate,Entry Time,Exit Time,Total Cost\n")
        f.write(report_data)
    return FileResponse(file_name)

