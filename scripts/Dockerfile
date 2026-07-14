# Multi-Asset SaaS Trading Platform Dockerfile
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    requests \
    cryptography \
    google-antigravity-sdk \
    python-dotenv

# Copy application code
COPY . /app

# Expose API gateway port
EXPOSE 8900

# Execute server process
CMD ["python", "saas_multi_api.py"]
