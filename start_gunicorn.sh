#!/bin/bash
# Gunicorn startup script for Lotus Electronics Chatbot API (Production)

echo "🚀 Starting Lotus Electronics Chatbot API with Gunicorn..."

# Disable Hugging Face tokenizer parallelism warning
export TOKENIZERS_PARALLELISM=false

# Run with Gunicorn for production
gunicorn app_production:app \
  --bind 0.0.0.0:8001 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 30 \
  --keep-alive 2 \
  --log-level info \
  --access-logfile - \
  --error-logfile -

echo "✅ Production server started at http://localhost:8001"
