FROM python:3.11-slim

WORKDIR /app

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копіювання файлів залежностей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіювання коду проекту
COPY . .

# Експонуємо порт для API
EXPOSE 8000

# За замовчуванням запускаємо API (Render Web Service)
# Для бота (Background Worker) команда буде перевизначена в render.yaml
CMD ["python", "api/main.py"]
