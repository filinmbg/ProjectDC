from src.entity.models import MovementLog, Payment
from sqlalchemy import func, select, desc


async def calculate_parking_duration(session, movement_log_id: int):
    try:
        movement_log = await session.get(MovementLog, movement_log_id)
        if movement_log.exit_time:
            # Якщо є час виїзду, обчислити різницю між часом виїзду та часом в'їзду
            duration = movement_log.exit_time - movement_log.entry_time
        else:
            # Якщо немає часу виїзду, обчислити різницю між поточним часом та часом в'їзду
            duration = func.now() - movement_log.entry_time
        return duration
    except Exception as e:
        # Обробка помилок та повернення загального повідомлення про помилку
        raise ValueError("Failed to calculate parking duration: " + str(e))



async def record_entry_exit_time(session, vehicle_id: int, entry: bool):
    try:
        if entry:
            # If it's an entry, create a new MovementLog entry with entry_time set to current time
            movement_log = MovementLog(
                vehicle_id=vehicle_id, entry_time=func.now())
            session.add(movement_log)
        else:
            # If it's an exit, find the latest MovementLog for the vehicle and update its exit_time to current time
            latest_log = await session.execute(select(MovementLog).filter(MovementLog.vehicle_id == vehicle_id).order_by(desc(MovementLog.entry_time)).limit(1))
            latest_log = latest_log.scalar_one_or_none()
            if latest_log:
                latest_log.exit_time = func.now()
            else:
                raise ValueError("No entry record found for the vehicle")
        await session.commit()
        return {"message": "Entry/exit time recorded successfully"}
    except Exception as e:
        # Catch any exceptions and return a generic error message
        return {"detail": str(e)}


async def calculate_parking_cost(session, movement_log_id: int, cost_per_hour: int):
    try:
        # Отримати запис MovementLog з бази даних за допомогою session.get()
        movement_log = await session.get(MovementLog, movement_log_id)

        # Обчислити тривалість паркування за допомогою вже існуючої функції
        duration = await calculate_parking_duration(session, movement_log_id)

        # Обчислити вартість паркування на основі тривалості та вартості за годину
        cost = (duration.total_seconds() / 3600) * cost_per_hour

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

        # Перевіряємо, чи є записи для вказаного автомобіля
        if movement_logs:
            for log in movement_logs:
                # Додати тривалість паркування з кожного запису
                total_duration += await calculate_parking_duration(session, log.id)
            return total_duration
        else:
            # Якщо немає записів, повернути 0
            return total_duration
    except Exception as e:
        # В разі виникнення помилки повернути None та зареєструвати помилку для подальшого аналізу
        print(f"Failed to calculate total parking duration: {str(e)}")
        return None
