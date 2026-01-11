#!/bin/bash
# Stop all MACAE system components

echo "🛑 Stopping MACAE Full System..."
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop process by PID file
stop_by_pid() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}  Stopping $service_name (PID: $pid)...${NC}"
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}  Force killing $service_name...${NC}"
                kill -9 "$pid"
            fi
        fi
        rm -f "$pid_file"
    fi
}

# Stop Backend API
echo -e "${YELLOW}🖥️  Stopping Backend API...${NC}"
stop_by_pid "Backend API" "/tmp/backend.pid"
pkill -f "uvicorn.*app.main:app" || true

# Stop MCP Servers
echo -e "${YELLOW}🔧 Stopping MCP Servers...${NC}"
stop_by_pid "Gmail MCP Server" "/tmp/gmail_mcp.pid"
stop_by_pid "Salesforce MCP Server" "/tmp/salesforce_mcp.pid"
stop_by_pid "Main MCP Server" "/tmp/main_mcp.pid"

# Kill any remaining MCP server processes
pkill -f "python.*mcp_server" || true

# Stop MongoDB
echo -e "${YELLOW}📊 Stopping MongoDB...${NC}"
if docker ps | grep -q "macae-mongodb"; then
    docker stop macae-mongodb
    echo -e "${GREEN}✅ MongoDB stopped${NC}"
else
    echo -e "${YELLOW}  MongoDB was not running${NC}"
fi

# Clean up any remaining processes on our ports
echo -e "${YELLOW}🧹 Cleaning up remaining processes...${NC}"
for port in 8000 9000 9001 9002; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo -e "${YELLOW}  Killing process on port $port...${NC}"
        lsof -ti:$port | xargs kill -9 || true
    fi
done

echo -e "${GREEN}✅ All MACAE system components have been stopped${NC}"