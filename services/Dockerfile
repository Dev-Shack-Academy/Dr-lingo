# Dockerfile for Medical Translation Services

# Base - Common dependencies and configuration

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies (shared across all stages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


# Builder - Install Python dependencies

FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*


COPY requirements-docker.txt .

# Install Python dependencies with cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user -r requirements-docker.txt


FROM base AS production

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local


ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]


# Development - With dev tools (optional)

FROM production AS development

# Install dev dependencies if needed
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user debugpy ipython
