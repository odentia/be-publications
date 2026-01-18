FROM python:3.11-slim

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

CMD ["uvicorn", "src.post_service.api.app:app", "--host", "0.0.0.0", "--port", "8000"]