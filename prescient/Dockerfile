FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Verify the module is importable
RUN python -c "import api.main; print('Module loaded OK')"

# Expose port (Railway uses $PORT)
EXPOSE 8000

# Use PORT env var from Railway, default 8000
CMD python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
