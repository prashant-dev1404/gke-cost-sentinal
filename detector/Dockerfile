FROM python:3.11-slim

RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/

USER appuser
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
