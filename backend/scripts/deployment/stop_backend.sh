#!/bin/bash
# Clean stop script for backend server

echo "🛑 Stopping MACAE Backend..."

# Find all processes using port 8000
PIDS=$(lsof -ti:8000 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "✅ No backend process running on port 8000"
    exit 0
fi

# Kill each process
for PID in $PIDS; do
    echo "   Killing process $PID..."
    kill -9 $PID 2>/dev/null
done

# Wait a moment and verify
sleep 1

# Check if port is now free
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "❌ Failed to stop backend - port 8000 still in use"
    exit 1
else
    echo "✅ Backend stopped successfully"
    exit 0
fi
