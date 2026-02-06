# Dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    # For python-magic
    libmagic1\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Development stage
FROM python:3.12-slim AS development

WORKDIR /app

# Install system dependencies for development
RUN apt-get update && apt-get install -y \
    gettext \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Ensure development dependencies are available (in case builder stage didn't install them properly)
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Create non-root user with configurable UID/GID
ARG HOST_UID=1000
ARG HOST_GID=1000
RUN groupadd -g ${HOST_GID} comuniza && \
    useradd -m -u ${HOST_UID} -g comuniza comuniza && \
    chown -R comuniza:comuniza /app
USER comuniza

# Copy application code
COPY --chown=comuniza:comuniza . .


# Production stage
FROM python:3.12-slim AS production

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user with configurable UID/GID
ARG HOST_UID=1000
ARG HOST_GID=1000
RUN groupadd -g ${HOST_GID} comuniza && \
    useradd -m -u ${HOST_UID} -g comuniza comuniza

# Create necessary directories as root before switching user
RUN mkdir -p /app/static /app/staticfiles /app/media /app/logs && \
    chown -R ${HOST_GID}:${HOST_GID} /app && \
    chmod -R 755 /app

# Copy application code
COPY --chown=${HOST_GID}:comuniza . .

# Switch to non-root user
USER comuniza

# Expose production port
EXPOSE 4002

# Default command (can be overridden)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:4002"]
