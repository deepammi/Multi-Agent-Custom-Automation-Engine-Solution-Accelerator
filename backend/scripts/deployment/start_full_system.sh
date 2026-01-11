#!/bin/bash
# Comprehensive startup script for MACAE Backend System
# This script starts MongoDB, all MCP servers, and the backend API

set -e  # Exit on any error

echo "🚀 Starting MACAE Full System..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -ti:$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for $service_name on port $port...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            echo -e "${GREEN}✅ $service_name is ready on port $port${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start on port $port after $max_attempts attempts${NC}"
    return 1
}

# Function to stop existing processes
cleanup_existing() {
    echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
    
    # Stop backend if running
    if check_port 8000; then
        echo "  Stopping backend on port 8000..."
        pkill -f "uvicorn.*app.main:app" || true
        sleep 2
    fi
    
    # Stop MCP servers if running
    for port in 9000 9001 9002; do
        if check_port $port; then
            echo "  Stopping MCP server on port $port..."
            pkill -f "python.*mcp_server.*$port" || true
            sleep 1
        fi
    done
    
    # Stop MongoDB container if running
    if docker ps | grep -q "macae-mongodb"; then
        echo "  Stopping MongoDB container..."
        docker stop macae-mongodb || true
        sleep 2
    fi
}

# Function to start MongoDB
start_mongodb() {
    echo -e "${BLUE}📊 Starting MongoDB...${NC}"
    
    # Check if MongoDB container exists
    if docker ps -a | grep -q "macae-mongodb"; then
        echo "  MongoDB container exists, starting it..."
        docker start macae-mongodb
    else
        echo "  Creating and starting MongoDB container..."
        docker run -d \
            --name macae-mongodb \
            -p 27017:27017 \
            -e MONGO_INITDB_DATABASE=macae_db \
            -v macae_mongodb_data:/data/db \
            mongo:7.0
    fi
    
    # Wait for MongoDB to be ready
    echo -e "${YELLOW}⏳ Waiting for MongoDB to be ready...${NC}"
    local attempt=1
    local max_attempts=30
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec macae-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ MongoDB is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ MongoDB failed to start after $max_attempts attempts${NC}"
    return 1
}

# Function to start MCP servers
start_mcp_servers() {
    echo -e "${BLUE}🔧 Starting MCP Servers...${NC}"
    
    cd ../src/mcp_server
    
    # Start Gmail MCP Server (port 9000)
    echo "  Starting Gmail MCP Server on port 9000..."
    python3 gmail_mcp_server.py --transport http --port 9000 > ../../logs/gmail_mcp.log 2>&1 &
    GMAIL_PID=$!
    
    # Start Salesforce MCP Server (port 9001)
    echo "  Starting Salesforce MCP Server on port 9001..."
    python3 salesforce_mcp_server.py --transport http --port 9001 > ../../logs/salesforce_mcp.log 2>&1 &
    SALESFORCE_PID=$!
    
    # Start Main MCP Server with Bill.com (port 9002)
    echo "  Starting Main MCP Server (Bill.com) on port 9002..."
    python3 mcp_server.py --transport http --port 9002 > ../../logs/main_mcp.log 2>&1 &
    MAIN_MCP_PID=$!
    
    cd ../../backend
    
    # Wait for all MCP servers to be ready
    wait_for_service "Gmail MCP Server" 9000
    wait_for_service "Salesforce MCP Server" 9001
    wait_for_service "Main MCP Server (Bill.com)" 9002
    
    # Store PIDs for cleanup
    echo $GMAIL_PID > /tmp/gmail_mcp.pid
    echo $SALESFORCE_PID > /tmp/salesforce_mcp.pid
    echo $MAIN_MCP_PID > /tmp/main_mcp.pid
    
    echo -e "${GREEN}✅ All MCP servers are running${NC}"
}

# Function to start backend
start_backend() {
    echo -e "${BLUE}🖥️  Starting Backend API...${NC}"
    
    # Set environment variables for MCP servers
    export MCP_GMAIL_URL="http://localhost:9000"
    export MCP_SALESFORCE_URL="http://localhost:9001"
    export MCP_MAIN_URL="http://localhost:9002"  # Main MCP with Bill.com
    export MONGODB_URL="mongodb://localhost:27017"
    export MONGODB_DATABASE="macae_db"
    
    # Start the backend server
    echo "  Starting FastAPI server on port 8000..."
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Store PID for cleanup
    echo $BACKEND_PID > /tmp/backend.pid
    
    # Wait for backend to be ready
    wait_for_service "Backend API" 8000
    
    echo -e "${GREEN}✅ Backend API is running${NC}"
}

# Function to show system status
show_status() {
    echo ""
    echo -e "${GREEN}🎉 MACAE System Status${NC}"
    echo "========================"
    echo -e "${GREEN}✅ MongoDB:${NC}           http://localhost:27017"
    echo -e "${GREEN}✅ Gmail MCP:${NC}         http://localhost:9000"
    echo -e "${GREEN}✅ Salesforce MCP:${NC}    http://localhost:9001"
    echo -e "${GREEN}✅ Main MCP (Bill.com):${NC} http://localhost:9002"
    echo -e "${GREEN}✅ Backend API:${NC}       http://localhost:8000"
    echo ""
    echo -e "${BLUE}📋 API Documentation:${NC}  http://localhost:8000/docs"
    echo -e "${BLUE}📊 Health Check:${NC}       http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}📝 Logs are available in:${NC}"
    echo "  - Backend:     logs/backend.log"
    echo "  - Gmail MCP:   logs/gmail_mcp.log"
    echo "  - Salesforce:  logs/salesforce_mcp.log"
    echo "  - Main MCP:    logs/main_mcp.log"
    echo ""
    echo -e "${YELLOW}🛑 To stop all services:${NC} ./stop_full_system.sh"
}

# Function to create logs directory
setup_logs() {
    mkdir -p logs
    echo -e "${BLUE}📁 Created logs directory${NC}"
}

# Main execution
main() {
    # Setup
    setup_logs
    
    # Cleanup existing processes
    cleanup_existing
    
    # Start services in order
    start_mongodb
    start_mcp_servers
    start_backend
    
    # Show final status
    show_status
    
    echo -e "${GREEN}🚀 MACAE Full System is now running!${NC}"
    echo -e "${YELLOW}💡 Press Ctrl+C to stop all services${NC}"
    
    # Keep script running and handle Ctrl+C
    trap 'echo -e "\n${YELLOW}🛑 Shutting down system...${NC}"; ./stop_full_system.sh; exit 0' INT
    
    # Keep the script running
    while true; do
        sleep 10
        # Check if all services are still running
        if ! check_port 8000 || ! check_port 9000 || ! check_port 9001 || ! check_port 9002; then
            echo -e "${RED}❌ One or more services have stopped. Check logs for details.${NC}"
            break
        fi
    done
}

# Run main function
main "$@"