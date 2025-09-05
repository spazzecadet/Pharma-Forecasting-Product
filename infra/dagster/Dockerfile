FROM python:3.11-slim

WORKDIR /opt/dagster/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /opt/dagster/app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /opt/dagster/app

# Expose Dagster ports
EXPOSE 3000 3001

# Run Dagster
CMD ["dagster", "dev", "--host", "0.0.0.0", "--port", "3000"]
