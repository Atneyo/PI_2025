

# Étape 2 : image backend
FROM python:3.11-slim

WORKDIR /app

COPY models/speech_to_text/requirements_stt.txt .
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements_stt.txt

# Installer ffmpeg système + dépendances nécessaires
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*


# Copier le code des modèles dans le backend
COPY models/ /app/models

# Installer les requirements modèles pour que Python puisse les importer
# COPY --from=models /usr/local/lib/python3.11 /usr/local/lib/python3.11

# Installer requirements backend
COPY interface/backend/requirements_backend.txt .
RUN pip install --no-cache-dir -r requirements_backend.txt

COPY ./interface/backend /app/interface/backend

# Lancer FastAPI # ajouter --reload pour le développement
CMD ["uvicorn", "interface.backend.main:app", "--host", "0.0.0.0", "--port", "8000"] 
