#!/bin/bash
# Clean start script for backend server

echo "🚀 Starting MACAE Backend..."

# Check if port 8000 is in use
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Stopping existing process..."
    ./stop_backend.sh
    sleep 2
fi

# Start the backend server
echo "✅ Starting backend on port 8000..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
