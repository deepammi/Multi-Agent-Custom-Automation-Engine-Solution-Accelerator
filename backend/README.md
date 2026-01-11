# Multi-Agent Custom Automation Engine - Backend

This is the backend service for the Multi-Agent Custom Automation Engine (MACAE), built with FastAPI and LangGraph for multi-agent workflow orchestration.

## Architecture

- **Framework**: FastAPI for REST API and WebSocket endpoints
- **Agent Orchestration**: LangGraph multi-agent collaboration pattern
- **Database**: MongoDB for document storage (plans, messages, teams, sessions)
- **Real-time Communication**: WebSocket for streaming agent responses
- **LLM Provider**: Configurable (Gemini, OpenAI, Anthropic, Ollama)
- **Tool Integration**: FastMCP server for external service integration

## Directory Structure

```
backend/
├── app/                          # Core application code
│   ├── api/                      # REST API endpoints
│   ├── agents/                   # Agent implementations
│   ├── services/                 # Business logic services
│   ├── models/                   # Data models
│   └── db/                       # Database layer
├── tests/                        # Organized test files
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── e2e/                      # End-to-end tests
│   └── property/                 # Property-based tests
├── scripts/                      # Utility scripts
│   ├── setup/                    # Environment setup
│   ├── debug/                    # Debug utilities
│   ├── deployment/               # Deployment scripts
│   └── maintenance/              # Maintenance tools
├── config/                       # Configuration files
├── docs/                         # Documentation
└── temp/                         # Temporary files (not committed)
```

## Quick Start

### Prerequisites

- Python 3.9+
- MongoDB
- Environment variables configured (see `.env.example`)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start MongoDB (if running locally):
```bash
mongod
```

4. Start the backend server:
```bash
./scripts/deployment/start_backend.sh
```

The API will be available at `http://localhost:8000`

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/   # Integration tests
python -m pytest tests/e2e/          # End-to-end tests
```

### Environment Setup

Use the setup scripts to configure your development environment:

```bash
# Set up MCP servers
python scripts/setup/setup_mcp_environment.py

# Configure LLM provider
python scripts/setup/setup_gemini.py

# Set up Gmail OAuth (if using Gmail integration)
python scripts/setup/setup_gmail_oauth.py
```

### Debug Tools

Debug utilities are available in `scripts/debug/`:

```bash
# Check database connectivity
python scripts/debug/debug_database.py

# Validate MCP configuration
python scripts/debug/validate_mcp_config.py

# Debug WebSocket flow
python scripts/debug/debug_websocket_flow.py
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `LLM_PROVIDER`: LLM provider (gemini, openai, anthropic, ollama)
- `MONGODB_URL`: MongoDB connection string
- `GOOGLE_API_KEY`: Google API key (for Gemini)
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key

### MCP Configuration

MCP (Model Context Protocol) servers are configured in `config/mcp_config.json`. See the MCP documentation for details on adding new tools and services.

## Deployment

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Production

Use the deployment scripts:

```bash
# Start full system (backend + MCP servers)
./scripts/deployment/start_full_system.sh

# Stop system
./scripts/deployment/stop_full_system.sh
```

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Use the debug tools for troubleshooting
4. Update documentation as needed

## Troubleshooting

Common issues and solutions:

1. **MongoDB Connection Issues**: Check `MONGODB_URL` in `.env`
2. **LLM Provider Errors**: Verify API keys and provider configuration
3. **MCP Server Issues**: Use `scripts/debug/validate_mcp_config.py`
4. **WebSocket Problems**: Check `scripts/debug/debug_websocket_flow.py`

For more detailed troubleshooting, see the debug scripts in `scripts/debug/`.