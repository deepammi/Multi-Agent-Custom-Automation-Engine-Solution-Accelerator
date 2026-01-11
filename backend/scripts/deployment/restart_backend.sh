#!/bin/bash
# Restart script for backend server

echo "🔄 Restarting MACAE Backend..."

# Stop the backend
./stop_backend.sh

# Wait a moment
sleep 2

# Start the backend
./start_backend.sh
