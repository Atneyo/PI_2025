

# backend image
FROM python:3.11-slim

WORKDIR /app

COPY models/speech_to_text/requirements_stt.txt .
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements_stt.txt
COPY monitoring/requirements.txt .
RUN pip install -r requirements.txt
COPY interface/backend/requirements_yolo_without_hat.txt .
RUN pip install -r requirements_yolo_without_hat.txt

# Install ffmpeg + necessary depedencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*


# Copy models code in backend
COPY models/ /app/models

# Copy monitoring code in backend
COPY monitoring/ /app/monitoring

# Install models requirements so python can import it
# COPY --from=models /usr/local/lib/python3.11 /usr/local/lib/python3.11

# Install backend requirements
COPY interface/backend/requirements_backend.txt .
RUN pip install --no-cache-dir -r requirements_backend.txt

COPY ./interface/backend /app/interface/backend

# Launch FastAPI # add --reload to dev
CMD ["uvicorn", "interface.backend.main:app", "--host", "0.0.0.0", "--port", "8000"] 
