# Multi-Agent Custom Automation Engine (MACAE)

A LangGraph-based multi-agent automation system for financial and business process automation.

## 🚀 Quick Start

```bash
# Setup development environment
./scripts/setup/start-dev.sh

# Or manually:
cd backend && python3 -m uvicorn app.main:app --reload
cd src/frontend && npm run dev
```

## 📁 Project Structure

```
├── backend/                 # FastAPI + LangGraph backend
├── src/                     # Frontend and MCP servers
│   ├── frontend/           # React TypeScript frontend
│   └── mcp_server/         # Model Context Protocol servers
├── tests/                  # Root-level integration tests
├── scripts/                # Development and setup scripts
├── config/                 # Configuration files and templates
├── docs/                   # Project documentation
├── logs/                   # Application logs (gitignored)
└── temp/                   # Temporary files (gitignored)
```

## 🤖 Agent Capabilities

- **Gmail Agent**: Email processing and automation
- **Accounts Payable Agent**: Invoice processing and validation
- **CRM Agent**: Customer relationship management
- **Audit Agent**: Compliance and audit automation
- **Contract Agent**: Contract analysis and management
- **Procurement Agent**: Procurement process automation

## 🔧 Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Docker (optional)

### Setup
1. Clone the repository
2. Run setup script: `./scripts/setup/start-dev.sh`
3. Configure environment variables (see `.env.example`)
4. Start development servers

### Testing
```bash
# Backend tests
cd backend && python3 -m pytest

# Frontend tests  
cd src/frontend && npm test

# Integration tests
python3 -m pytest tests/
```

## 📚 Documentation

- [Quick Start Guide](docs/project/QUICK_START.md)
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](src/frontend/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🏗️ Architecture

Built on:
- **Backend**: FastAPI + LangGraph + MongoDB
- **Frontend**: React + TypeScript + Fluent UI
- **Agents**: LangGraph multi-agent collaboration
- **Tools**: FastMCP server integration
- **Real-time**: WebSocket streaming

## 🤝 Contributing

1. Follow the existing code organization
2. Run tests before committing
3. Update documentation for new features
4. Use the provided development scripts

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
