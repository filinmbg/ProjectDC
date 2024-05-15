import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sendgrid import SendGridAPIClient, Mail
from sqlalchemy import text, select, or_
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from src.conf.config import config
from src.database.db import get_db
from src.entity.models import MovementLog, User
from src.routes import auth_routes, vehicles_routes, user_routes
import time
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
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory='templates')


@app.get("/", response_class=HTMLResponse, description="Project DC", tags=["Main index.html"])
async def root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "title": "Project DC"})


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


async def start_send_notice():
    async for db in get_db():
        await send_notice(db)


async def send_notice(session):
    while True:
        movement_logs = await session.execute(
            select(MovementLog).filter(or_(
                MovementLog.status != "+",
                MovementLog.status.is_(None)
            ))
        )
        movement_logs = movement_logs.scalars().all()
        for log in movement_logs:
            if datetime.now() - log.entry_time > timedelta(hours=1):
                user = await session.execute(select(User).filter(User.id == log.user_id))
                user = user.scalars().first()
                if user:
                    notification_message = f"Шановний {user.username},\n\nМи хочемо повідомити Вам, що час безкоштовної години на парковці закінчився. Якщо Ви продовжите перебування на парковці, буде нарахована плата за додатковий час.\n\nЗ повагою,\nКоманда парковки"
                    await send_email("dizir7772@ukr.net", user.email, "Сповіщення", notification_message)
                    log.status = "+"
        await session.commit()
        await asyncio.sleep(10)


async def send_email(sender_email, recipient_email, subject, message):
    sg_api_key = config.TWILIO_API_KEY_EMAIL_SENDER
    if not sg_api_key:
        print("Не знайдено API ключ SendGrid.")
        return
    try:
        mail = Mail(
            from_email=sender_email,
            to_emails=recipient_email,
            subject=subject,
            plain_text_content=message)
        sg = SendGridAPIClient(sg_api_key)
        response = sg.send(mail)
        if response.status_code == 202:
            print("Повідомлення успішно надіслано.")
        else:
            print("Помилка під час надсилання повідомлення. Код відповіді:", response.status_code)
    except Exception as e:
        print("Виникла помилка при відправленні повідомлення:", str(e))


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_send_notice())


app.include_router(auth_routes.router, prefix="/api")
app.include_router(vehicles_routes.router)
app.include_router(user_routes.router)
