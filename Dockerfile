# Використовуємо офіційний базовий образ Python з встановленим python-3.11
FROM python:3.11

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Встановимо необхідний пакунок libgl1-mesa-glx
RUN apt-get update && apt-get install -y libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# Встановимо залежності всередині контейнера
COPY pyproject.toml poetry.lock $APP_HOME/
COPY src/ $APP_HOME/src/
COPY main.py $APP_HOME/

# Встановимо залежності за допомогою Poetry
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root

# Вказуємо порт, де працює застосунок всередині контейнера
EXPOSE 8000

# Запускаємо наш застосунок всередині контейнера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
