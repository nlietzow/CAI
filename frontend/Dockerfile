# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (like ffmpeg for audio processing)
# This command updates the package list, installs ffmpeg, and then cleans up
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable using the recommended key=value syntax
ENV PORT=8501

# Run the app when the container launches
CMD ["streamlit", "run", "cai_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]