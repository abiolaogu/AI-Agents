FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8777
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8777", "--workers", "4"]
