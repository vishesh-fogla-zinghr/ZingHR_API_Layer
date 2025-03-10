# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ODBC driver
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    curl \
    gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip  && \
    pip install --no-cache-dir redis==5.0.1



# Copy requirements first to leverage Docker cache
COPY requirements.txt .


ENV PYTHONPATH=/app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 