# Use the official Python image as base
FROM python:3.11-slim-buster

# Set the working directory
WORKDIR /app

# Copy only the necessary files to the container
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the files to the container
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# Start the application
CMD ["python", "bot.py"]