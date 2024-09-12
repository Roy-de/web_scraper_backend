# Use the official Python image
FROM python:3.11

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libxi6 \
    libgconf-2-4 \
    cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver

# Copy the cleanup script
COPY cleanup.sh /usr/local/bin/cleanup.sh
RUN chmod +x /usr/local/bin/cleanup.sh

# Copy the crontab file
COPY crontab /etc/cron.d/cleanup-cron
RUN chmod 0644 /etc/cron.d/cleanup-cron && crontab /etc/cron.d/cleanup-cron

# Set the display port to avoid crashes
ENV DISPLAY=:99

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8080

# Start cron service and FastAPI app
CMD ["sh", "-c", "cron && uvicorn main:app --host 0.0.0.0 --port 8080 --reload"]