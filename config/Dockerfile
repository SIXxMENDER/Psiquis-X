# Base Image (Slim for size)
FROM python:3.10-slim

# Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set Working Directory
WORKDIR /app

# Install System Dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Browsers (Heavy step)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy Project Code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI Port
EXPOSE 8001

# Default Command
CMD ["python", "server_v2.py"]
