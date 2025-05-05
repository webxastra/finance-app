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

# Create NLTK data directory
RUN mkdir -p /app/nltk_data && chmod -R 777 /app/nltk_data

# Copy application code
COPY . .

# Make setup.py executable
RUN chmod +x /app/ai_modules/expense_categorizer/setup.py

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Running NLTK setup..."\n\
python /app/ai_modules/expense_categorizer/setup.py\n\
echo "Starting Gunicorn server..."\n\
exec gunicorn --bind 0.0.0.0:5000 "app:create_app()" --workers 3' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

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

# Run the application with our entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 