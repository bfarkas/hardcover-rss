FROM python:3.11-slim as builder

# Add metadata labels
LABEL org.opencontainers.image.source="https://github.com/hideki23/hardcover_rss"
LABEL org.opencontainers.image.description="Hardcover RSS Service - Generate RSS feeds from Hardcover want-to-read lists"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Debug: List installed packages
RUN pip list | grep uvicorn

FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Debug: Verify uvicorn is available
RUN python3 -c "import uvicorn; print('uvicorn version:', uvicorn.__version__)"

# Copy application code
COPY app/ ./app/
COPY config/ ./config/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 