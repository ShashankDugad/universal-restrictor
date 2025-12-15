# Universal Restrictor - Docker Image
# 
# Build:  docker build -t universal-restrictor .
# Run:    docker run -p 8000:8000 universal-restrictor

# ==============================================================================
# Stage 1: Base image with Python
# ==============================================================================
FROM python:3.11-slim as base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# ==============================================================================
# Stage 2: Builder - install dependencies
# ==============================================================================
FROM base as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies (skip torch for smaller image - uses keyword fallback for toxicity)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi>=0.100.0 \
    uvicorn>=0.22.0 \
    pydantic>=2.0.0 \
    python-multipart>=0.0.6

# ==============================================================================
# Stage 3: Production image
# ==============================================================================
FROM base as production

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy application code
COPY --chown=appuser:appuser restrictor/ /app/restrictor/
COPY --chown=appuser:appuser pyproject.toml /app/

# Install the package
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the server
CMD ["uvicorn", "restrictor.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
