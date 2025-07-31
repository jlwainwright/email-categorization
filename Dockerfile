# Multi-stage build for optimized Python email categorization system
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION=1.2.0
ARG VCS_REF

# Add metadata labels
LABEL maintainer="Jacques Wainwright <jacques@sunlec.solar>" \
      org.label-schema.name="AI Email Categorization System" \
      org.label-schema.description="AI-powered email categorization using HuggingFace and OpenAI" \
      org.label-schema.version="${VERSION}" \
      org.label-schema.build-date="${BUILD_DATE}" \
      org.label-schema.vcs-ref="${VCS_REF}" \
      org.label-schema.schema-version="1.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r emailcat && useradd -r -g emailcat -d /app -s /bin/bash emailcat

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=emailcat:emailcat . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
    && chown -R emailcat:emailcat /app

# Make scripts executable
RUN chmod +x /app/*.sh /app/email_categorizer_dry_run.py

# Switch to non-root user
USER emailcat

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Africa/Johannesburg

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Expose ports for web interface and metrics
EXPOSE 8082 8000

# Default command - run continuous mode
CMD ["python3", "email_categorizer_continuous.py", "300"]