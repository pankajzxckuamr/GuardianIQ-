# ==============================================================================
# GuardianIQ Backend Dockerfile (Multi-stage Production Image)
# ==============================================================================

# Stage 1: Build & wheels preparation
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels gunicorn

# Stage 2: Final lightweight runtime image
FROM python:3.10-slim AS runner

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install runtime dependencies (e.g. libpq for psycopg2, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Create non-root system user
RUN groupadd -r guardianiq && useradd -r -g guardianiq -d /app -s /sbin/nologin guardianiq

# Copy application source code
COPY . /app

# Ensure entrypoint is executable and set correct permissions
RUN chmod +x /app/entrypoint.sh && \
    chown -R guardianiq:guardianiq /app

USER guardianiq

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
