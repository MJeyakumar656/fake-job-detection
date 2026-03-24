FROM python:3.11-slim

# Install system dependencies, Chromium, and ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data during build so runtime imports don't stall
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN mkdir -p ${NLTK_DATA} && \
    python -m nltk.downloader -d ${NLTK_DATA} \
    punkt \
    stopwords \
    averaged_perceptron_tagger \
    punkt_tab

# Copy application source code
COPY . .

# Set environment variables for Flask and Selenium
ENV PORT=10000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 10000

# Start gunicorn, generous timeout for Render
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 2 --timeout 300
