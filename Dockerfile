# Use the official Python image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Create a non-root user and set the user
RUN useradd -ms /bin/sh myuser

# Copy requirements.txt and install dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Change ownership of the /app directory to the non-root user
RUN chown -R myuser:myuser /app

# Switch to the non-root user
USER myuser

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
