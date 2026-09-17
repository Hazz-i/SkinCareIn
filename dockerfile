FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client libs and OpenCV requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml project.toml* ./
RUN pip install --no-cache-dir --upgrade pip && \
    python -c "import tomllib; reqs = tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']; open('requirements.tmp', 'w').write('\n'.join(reqs))" && \
    pip install --no-cache-dir -r requirements.tmp && \
    rm requirements.tmp

COPY . .
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8000

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
