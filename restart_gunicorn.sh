#!/bin/bash
# Restart Gunicorn server script

echo "🔄 Restarting Lotus Electronics Chatbot API..."

# Stop the existing server
./stop_gunicorn.sh

# Wait a moment
sleep 2

# Start the server again
./start_gunicorn.sh

echo "🎉 Server restart complete!"
