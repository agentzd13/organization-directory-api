# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any needed for asyncpg/sqlite)
# For sqlite and slim, usually fine.

# Copy requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Exposure port
EXPOSE 8000

# Command to run the application
# Use host 0.0.0.0 to be accessible outside container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
