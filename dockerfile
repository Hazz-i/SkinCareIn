# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Install only necessary packages for production
RUN pip install --no-cache-dir \
    fastapi==0.115.13 \
    uvicorn==0.34.3 \
    pydantic==2.11.7 \
    python-dotenv==1.1.0 \
    requests==2.32.4 \
    pillow==11.2.1 \
    torch \
    torchvision \
    google-genai==1.21.1

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models utils

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
