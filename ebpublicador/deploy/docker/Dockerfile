# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=docker \
    DEBUG=false \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/storage/uploads \
             /app/storage/generated \
             /app/storage/cache \
             /app/storage/logs \
             /app/web/assets \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Ensure directories exist with fallback\n\
mkdir -p /app/storage/{uploads,generated,cache,logs} 2>/dev/null || mkdir -p /tmp/storage/{uploads,generated,cache,logs}\n\
\n\
# Initialize database if needed\n\
if [ "$DATABASE_URL" != "" ]; then\n\
    echo "Initializing database..."\n\
    python -c "from api.core.database import init_db; init_db()" || echo "Database initialization skipped"\n\
fi\n\
\n\
# Start the application\n\
echo "Starting EBPublicador..."\n\
exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-1}\n\
' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown appuser:appuser /app/start.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start application
CMD ["/app/start.sh"]

# Labels for metadata
LABEL maintainer="EBPublicador Team" \
      version="1.0.0" \
      description="AI-Powered Content Management System" \
      org.opencontainers.image.source="https://github.com/your-repo/ebpublicador"