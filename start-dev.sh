#!/bin/bash

# Development startup script for LangGraph backend + React frontend
# This script starts both the backend and frontend in development mode

set -e

echo "=========================================="
echo "Starting Multi-Agent Automation Engine"
echo "LangGraph Backend + React Frontend"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend dependencies are installed
echo -e "${BLUE}Checking backend dependencies...${NC}"
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Backend virtual environment found${NC}"
fi

# Check if frontend dependencies are installed
echo -e "${BLUE}Checking frontend dependencies...${NC}"
if [ ! -d "src/frontend/node_modules" ]; then
    echo -e "${YELLOW}Node modules not found. Installing...${NC}"
    cd src/frontend
    npm install
    cd ../..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Frontend node_modules found${NC}"
fi

# Check if MongoDB is running
echo -e "${BLUE}Checking MongoDB...${NC}"
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}⚠ MongoDB not running. Please start MongoDB first:${NC}"
    echo "   brew services start mongodb-community"
    echo "   OR"
    echo "   docker run -d -p 27017:27017 mongo:latest"
    echo ""
    read -p "Press Enter when MongoDB is running, or Ctrl+C to exit..."
fi
echo -e "${GREEN}✓ MongoDB is running${NC}"

echo ""
echo "=========================================="
echo "Starting Services"
echo "=========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${BLUE}Starting backend on http://localhost:8000${NC}"
cd backend
source venv/bin/activate
python -m app.main > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠ Backend taking longer than expected. Check backend.log${NC}"
    fi
    sleep 1
done

# Start frontend
echo -e "${BLUE}Starting frontend on http://localhost:3000${NC}"
cd src/frontend
npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

echo ""
echo "=========================================="
echo -e "${GREEN}✓ All services started!${NC}"
echo "=========================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
