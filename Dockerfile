# Use Python 3.11 slim image (better SSL compatibility)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including SSL certificates
RUN apt-get update && apt-get install -y \
    gcc \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# Create empty __init__.py files if needed
RUN touch backend/__init__.py backend/config/__init__.py backend/models/__init__.py backend/services/__init__.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
