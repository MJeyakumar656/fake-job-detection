FROM python:3.11-slim

# Install system dependencies, Chromium, ChromeDriver, and Unzip
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download and UNZIP NLTK data during build
ENV NLTK_DATA=/opt/render/nltk_data
RUN mkdir -p ${NLTK_DATA} && \
    python -m nltk.downloader -d ${NLTK_DATA} punkt stopwords averaged_perceptron_tagger punkt_tab && \
    cd ${NLTK_DATA}/tokenizers && unzip -o punkt.zip && unzip -o punkt_tab.zip && rm *.zip || true && \
    cd ${NLTK_DATA}/corpora && unzip -o stopwords.zip && rm *.zip || true

# Copy application source code
COPY . .

# Set environment variables for Flask and Selenium
ENV PORT=10000
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 10000

# Start gunicorn, generous timeout for Render
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 2 --timeout 300
