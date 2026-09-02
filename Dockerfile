FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install freelancer-core first (shared library)
COPY freelancer-core /freelancer-core
COPY packages/core-auth /core-auth
RUN pip install --no-cache-dir /freelancer-core /core-auth

# Copy application requirements and install
COPY freelancer-leadtools/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY freelancer-leadtools ./freelancer-leadtools

WORKDIR /app/freelancer-leadtools

# Set environment variables
ENV PYTHONPATH=/app/freelancer-leadtools
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
