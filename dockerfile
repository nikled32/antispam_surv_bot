# Используем официальный образ Python
FROM python:3.9-slim

# Рабочая директория
WORKDIR /app
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запускаем бота
CMD ["python", "main.py"]