FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create instance directory for logs and data
RUN mkdir -p instance/logs instance/ai

# Create NLTK data directory and ensure proper permissions
RUN mkdir -p /app/nltk_data \
    && python -c "import nltk; nltk.download('stopwords', download_dir='/app/nltk_data'); nltk.download('wordnet', download_dir='/app/nltk_data'); nltk.download('omw-1.4', download_dir='/app/nltk_data'); nltk.download('punkt', download_dir='/app/nltk_data')" \
    && chmod -R 777 /app/nltk_data

# Verify NLTK data
RUN python -c "import nltk; nltk.data.path.append('/app/nltk_data'); print('NLTK data path:', nltk.data.path); from nltk.corpus import stopwords; print('Stopwords available:', len(stopwords.words('english')) > 0)"

# Copy application code
COPY . .

# Create a health check script
RUN echo '#!/bin/bash\n\
if curl -s http://localhost:5000/health > /dev/null; then\n\
  exit 0\n\
else\n\
  exit 1\n\
fi' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Expose the application port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1
ENV NLTK_DATA=/app/nltk_data

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()", "--workers", "3"] 