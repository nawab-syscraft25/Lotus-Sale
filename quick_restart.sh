#!/bin/bash
# Quick restart script for development

echo "🔄 Quick restart..."

# Kill existing Gunicorn processes
pkill -f "gunicorn.*app:app"

# Wait a moment
sleep 2

# Start again
bash start_gunicorn.sh

echo "✅ Restart complete!"
