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

# Встановлюємо PYTHONPATH, щоб імпорти працювали правильно
ENV PYTHONPATH=/app

# Експонуємо порт для API (Railway автоматично підставить PORT)
EXPOSE 8000

# За замовчуванням запускаємо API через uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
