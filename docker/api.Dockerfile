# Placeholder Dockerfile for API service
FROM python:3.10-slim
WORKDIR /app
COPY api /app/api
RUN pip install fastapi uvicorn sqlmodel sqlalchemy psycopg2-binary pydantic prometheus-fastapi-instrumentator slowapi python-multipart
ENV API_PORT=3004
EXPOSE 3004
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "3004"]
