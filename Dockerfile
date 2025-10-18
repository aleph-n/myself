# Dockerfile for the "myself" api service

# 1. Use an official lightweight Python image as a parent image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first to leverage Docker's build cache
COPY requirements.txt requirements.txt

# 4. Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application's code into the container
# This includes your 'src', 'data', and 'output' directories
COPY . .

# 6. Define the default command to run when the container starts.
# This will start the FastAPI server once you've implemented it in src/main.py.
# The host 0.0.0.0 makes the server accessible from outside the container.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]