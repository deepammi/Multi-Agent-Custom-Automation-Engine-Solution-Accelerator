# Quick Start Guide

## Prerequisites

- Python 3.9+
- Node.js 16+
- MongoDB (running on localhost:27017)

## Option 1: Automated Start (Recommended)

```bash
./start-dev.sh
```

This script will:
- Check and install dependencies
- Start MongoDB (if needed)
- Start backend on http://localhost:8000
- Start frontend on http://localhost:3000

## Option 2: Manual Start

### 1. Start MongoDB

```bash
# Using Homebrew
brew services start mongodb-community

# OR using Docker
docker run -d -p 27017:27017 mongo:latest
```

### 2. Start Backend

```bash
cd backend
python -m app.main
```

Backend will start on http://localhost:8000

### 3. Start Frontend

```bash
cd src/frontend
npm install  # First time only
npm start
```

Frontend will start on http://localhost:3000

## Verify Installation

### Backend Health Check

```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Run Backend Tests

```bash
cd backend
python test_e2e.py
# All tests should pass
```

## Using the Application

1. Open browser to http://localhost:3000
2. Enter a task description:
   - "Check invoice payment status"
   - "Perform closing reconciliation"
   - "Review audit evidence"
3. Click Submit
4. Watch agents analyze and process the task
5. Approve the plan when prompted
6. See the specialized agent complete the task

## Configuration

Frontend configuration is in:
- `src/frontend/public/config.json` - Runtime config
- `src/frontend/.env` - Environment variables

Backend configuration is in:
- `backend/.env` - Environment variables

## Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check MongoDB is running
mongosh --eval "db.version()"
```

### Frontend won't start

```bash
# Check if port 3000 is in use
lsof -i :3000

# Clear node_modules and reinstall
cd src/frontend
rm -rf node_modules package-lock.json
npm install
```

### WebSocket connection fails

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check browser console for errors
3. Verify config.json has correct API_URL

## Next Steps

- Read [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md) for detailed integration info
- Read [backend/PHASE_6_COMPLETE.md](./backend/PHASE_6_COMPLETE.md) for backend architecture
- Proceed to Phase 7 (Tool Integration) for MCP server integration

## Support

If you encounter issues:
1. Check logs: `backend.log` and `frontend.log`
2. Run tests: `cd backend && python test_e2e.py`
3. Review troubleshooting section above
4. Check [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md)
