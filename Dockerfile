# 1) Base image: lightweight Python runtime
FROM python:3.11-slim

# 2) Make container logs appear immediately (useful in deployment)
ENV PYTHONUNBUFFERED=1

# 3) Create a working directory inside the container
WORKDIR /app

# 4) Copy only requirements first (Docker caching trick)
COPY requirements.txt .

# 5) Install dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 6) Copy the rest of the project files
COPY . .

# 7) Expose the port the app will listen on (documentation + some platforms use it)
EXPOSE 8080

# 8) Start the FastAPI app with uvicorn
# IMPORTANT: host 0.0.0.0 is required for Docker
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

