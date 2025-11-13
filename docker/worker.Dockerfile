# Placeholder Dockerfile for Aforos worker
FROM python:3.10-slim
WORKDIR /app
COPY worker /app/worker
COPY worker/yolo_carla_pipeline /app/yolo_carla_pipeline
COPY worker/core /app/core
RUN pip install fastapi uvicorn numpy pandas scikit-learn filterpy opencv-python
ENV PORT=3001
EXPOSE 3001
CMD ["uvicorn", "worker.serve_aforos:app", "--host", "0.0.0.0", "--port", "3001"]
