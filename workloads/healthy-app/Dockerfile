FROM python:3.11-slim

RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app
COPY app.py .

RUN pip install --no-cache-dir fastapi uvicorn[standard]

USER appuser

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
