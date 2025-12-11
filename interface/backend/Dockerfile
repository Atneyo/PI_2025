# Slim version of python
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . .

# Expose port (FastAPI)
EXPOSE 8000

# Run app (FastAPI with uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
