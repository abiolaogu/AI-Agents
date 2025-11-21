FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8502
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8502", "--workers", "4"]
