FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r restrictor && useradd -r -g restrictor restrictor

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY restrictor/ ./restrictor/
COPY run.sh .

# Create data directory for audit logs
RUN mkdir -p /data && chown -R restrictor:restrictor /data

# Set ownership
RUN chown -R restrictor:restrictor /app

# Switch to non-root user
USER restrictor

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "restrictor.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
