from datetime import datetime
import csv
from typing import List
from src.entity.models import MovementLog, Payment, User, Vehicle
from sqlalchemy import func, select, desc

async def convert_seconds_to_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours} годин {minutes} хвилин {seconds} секунд"


async def calculate_parking_duration(session, movement_log_id: int):
    try:
        movement_log = await session.get(MovementLog, movement_log_id)
        if movement_log.exit_time:
            # Якщо є час виїзду, обчислити різницю між часом виїзду та часом в'їзду
            duration = movement_log.exit_time - movement_log.entry_time
        else:
            # Якщо немає часу виїзду, обчислити різницю між поточним часом та часом в'їзду
            duration = datetime.now() - movement_log.entry_time
        return duration
    except Exception as e:
        # Обробка помилок та повернення загального повідомлення про помилку
        raise ValueError("Failed to calculate parking duration: " + str(e))


async def record_entry_exit_time(session, vehicle_id: int, entry: bool, user_id: int = None):
    try:
        if entry:
            # If it's an entry, create a new MovementLog entry with entry_time set to current time
            movement_log = MovementLog(vehicle_id=vehicle_id, entry_time=datetime.now(), user_id=user_id)
            session.add(movement_log)
        else:
            # If it's an exit, find the latest MovementLog for the vehicle and update its exit_time to current time
            latest_log = await session.execute(
                select(MovementLog).filter(MovementLog.vehicle_id == vehicle_id).order_by(
                    desc(MovementLog.entry_time)).limit(1))
            latest_log = latest_log.scalar_one_or_none()
            if latest_log:
                latest_log.exit_time = datetime.now()
            else:
                raise ValueError("No entry record found for the vehicle")
        await session.commit()
        return {"message": "Entry/exit time recorded successfully"}
    except Exception as e:
        # Catch any exceptions and return a generic error message
        return {"detail": str(e)}


async def calculate_parking_cost(session, movement_log_id: int, cost_per_hour=10, free_time=3600):
    try:
        # Отримати запис MovementLog з бази даних за допомогою session.get()
        movement_log = await session.get(MovementLog, movement_log_id)

        # Обчислити тривалість паркування за допомогою вже існуючої функції
        duration = await calculate_parking_duration(session, movement_log_id)
        if duration.total_seconds() > free_time:
            # Обчислити вартість паркування на основі тривалості та вартості за годину
            cost = (duration.total_seconds() - free_time) / 3600 * cost_per_hour
        else:
            cost = 0
        # Оновити запис оплати з обчисленою сумою
        payment = Payment(user_id=movement_log.user_id,
                          cost_per_hour=cost_per_hour, amount=cost)
        session.add(payment)
        await session.commit()

        return cost
    except Exception as e:
        # В разі виникнення помилки повернути None та зареєструвати помилку для подальшого аналізу
        print(f"Failed to calculate parking cost: {str(e)}")
        return None


async def calculate_total_parking_duration(session, vehicle_id: int):
    try:
        total_duration = 0
        movement_logs = await session.execute(select(MovementLog).filter(MovementLog.vehicle_id == vehicle_id))
        movement_logs = movement_logs.scalars().all()
        # Перевіряємо, чи є записи для вказаного автомобіля
        if movement_logs:
            for log in movement_logs:
                parking_duration = await calculate_parking_duration(session, log.id)
                total_seconds = parking_duration.days * 24 * 60 * 60 + parking_duration.seconds + parking_duration.microseconds / 1000000
                total_duration += int(total_seconds)
            return await convert_seconds_to_time(total_duration)
        else:
            # Якщо немає записів, повернути 0
            return total_duration
    except Exception as e:
        # В разі виникнення помилки повернути None та зареєструвати помилку для подальшого аналізу
        print(f"Failed to calculate total parking duration: {str(e)}")
        return None


async def generate_payment_report(session):
    try:
        # Отримати список оплат з бази даних
        payments = await session.execute(select(Payment))
        payments = payments.scalars().all()

        # Створити ім'я файлу звіту з поточною датою та часом
        report_file_name = f"payment_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

        # Відкрити CSV-файл для запису
        with open(report_file_name, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Записати заголовки стовпців у файл
            writer.writerow(
                ["Payment ID", "User ID", "Cost per Hour", "Amount", "Payment Datetime"])

            # Записати дані про оплати у файл
            for payment in payments:
                writer.writerow([payment.id, payment.user_id, payment.cost_per_hour,
                                 payment.amount, payment.payment_datetime])

        return report_file_name
    except Exception as e:
        # В разі виникнення помилки повернути None та зареєструвати помилку для подальшого аналізу
        print(f"Failed to generate payment report: {str(e)}")
        return None


async def generate_payment_report_for_vehicle(session, vehicle_id: int) -> str:
    try:
        # Отримуємо список оплат для вказаного автомобіля
        payments: List[Payment] = await session.execute(
            select(Payment).join(User).join(
                Vehicle).filter(Vehicle.id == vehicle_id)
        )
        payments = payments.scalars().all()

        # Створюємо ім'я файлу для звіту
        file_name = f"payment_report_for_vehicle_{vehicle_id}.csv"

        # Відкриваємо файл для запису у форматі CSV
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Записуємо заголовки у файл
            writer.writerow(
                ['Payment ID', 'User ID', 'Cost Per Hour', 'Amount', 'Payment Datetime'])

            # Записуємо дані про кожну оплату у файл
            for payment in payments:
                try:
                    writer.writerow([payment.id, payment.user_id, payment.cost_per_hour,
                                     payment.amount, payment.payment_datetime])
                except Exception as e:
                    print(f"Failed to write payment data to CSV: {str(e)}")

        return file_name
    except Exception as e:
        raise ValueError(
            f"Failed to generate payment report for vehicle: {str(e)}")
