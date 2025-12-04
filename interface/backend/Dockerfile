# Utiliser une image Python légère
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Exposer le port (ex: FastAPI par défaut)
EXPOSE 8000

# Commande pour lancer l'app (FastAPI en uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
