#!/usr/bin/env python3
"""
Root Directory Organization Script
Organizes the Multi-Agent Custom Automation Engine root directory for GitHub readiness.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import json
from datetime import datetime

class RootDirectoryOrganizer:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.backup_dir = self.root_path / "temp" / "organization_backup"
        self.organization_log = []
        
    def log_action(self, action: str, source: str, destination: str = ""):
        """Log organization actions for review"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "source": source,
            "destination": destination
        }
        self.organization_log.append(entry)
        print(f"[{action}] {source} -> {destination}")
    
    def create_directory_structure(self):
        """Create the organized directory structure"""
        directories = [
            "tests/root",
            "tests/integration", 
            "scripts/integration",
            "scripts/setup",
            "config/secrets",
            "temp/logs",
            "temp/test_results", 
            "docs/project",
            "tools/development"
        ]
        
        for directory in directories:
            dir_path = self.root_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.log_action("CREATE_DIR", str(directory))
    
    def organize_test_files(self):
        """Move scattered test files to tests/root/"""
        test_files = [
            "test_bill_com_real.py",
            "test_bill_com_real_api.py", 
            "test_detailed_invoice_retrieval.py",
            "test_integration_simple.py"
        ]
        
        target_dir = self.root_path / "tests" / "root"
        
        for test_file in test_files:
            source = self.root_path / test_file
            if source.exists():
                destination = target_dir / test_file
                shutil.move(str(source), str(destination))
                self.log_action("MOVE", test_file, f"tests/root/{test_file}")
    
    def organize_log_files(self):
        """Move log files to temp/logs/"""
        log_files = [
            "backend.log",
            "frontend.log", 
            "salesforce_server.log"
        ]
        
        target_dir = self.root_path / "temp" / "logs"
        
        for log_file in log_files:
            source = self.root_path / log_file
            if source.exists():
                destination = target_dir / log_file
                shutil.move(str(source), str(destination))
                self.log_action("MOVE", log_file, f"temp/logs/{log_file}")
    
    def organize_config_files(self):
        """Move configuration files to config/"""
        config_files = [
            ("client_secret.json", "config/secrets/client_secret.json"),
            ("SAMPLE_TEAM_CONFIGURATION.json", "config/SAMPLE_TEAM_CONFIGURATION.json"),
            (".flake8", "config/.flake8")
        ]
        
        for source_file, target_path in config_files:
            source = self.root_path / source_file
            destination = self.root_path / target_path
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                self.log_action("MOVE", source_file, target_path)
    
    def organize_scripts(self):
        """Organize existing scripts directory"""
        scripts_dir = self.root_path / "scripts"
        if scripts_dir.exists():
            # Move existing scripts to integration subdirectory
            integration_dir = scripts_dir / "integration"
            integration_dir.mkdir(exist_ok=True)
            
            for script_file in scripts_dir.glob("*.py"):
                if script_file.parent == scripts_dir:  # Only move files directly in scripts/
                    destination = integration_dir / script_file.name
                    shutil.move(str(script_file), str(destination))
                    self.log_action("MOVE", f"scripts/{script_file.name}", f"scripts/integration/{script_file.name}")
        
        # Move start-dev.sh to scripts/setup/
        start_script = self.root_path / "start-dev.sh"
        if start_script.exists():
            setup_dir = scripts_dir / "setup"
            setup_dir.mkdir(parents=True, exist_ok=True)
            destination = setup_dir / "start-dev.sh"
            shutil.move(str(start_script), str(destination))
            self.log_action("MOVE", "start-dev.sh", "scripts/setup/start-dev.sh")
    
    def organize_documentation(self):
        """Organize documentation files"""
        doc_files = [
            ("Msft_Multi-Agent-Accl-README.md", "docs/project/Microsoft_Multi_Agent_Accelerator_README.md"),
            ("PRE_COMMIT_HOOK_README.md", "docs/project/PRE_COMMIT_HOOK_README.md"),
            ("QUICK_START.md", "docs/project/QUICK_START.md")
        ]
        
        for source_file, target_path in doc_files:
            source = self.root_path / source_file
            destination = self.root_path / target_path
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                self.log_action("MOVE", source_file, target_path)
    
    def update_gitignore(self):
        """Update .gitignore with new temporary directories"""
        gitignore_path = self.root_path / ".gitignore"
        
        additional_ignores = [
            "",
            "# Root directory organization",
            "temp/",
            "*.log",
            "test_results_*.json",
            "trace_*.json",
            "",
            "# Secrets and sensitive files", 
            "config/secrets/",
            "client_secret.json",
            "",
            "# Development tools",
            "tools/development/temp/",
        ]
        
        with open(gitignore_path, 'a') as f:
            f.write('\n'.join(additional_ignores))
        
        self.log_action("UPDATE", ".gitignore", "Added root organization ignores")
    
    def create_readme_files(self):
        """Create README files for organized directories"""
        readme_contents = {
            "tests/README.md": """# Root Level Tests

This directory contains test files that were originally in the root directory.

## Structure

- `root/` - Test files that were scattered in the project root
- `integration/` - Integration tests that span multiple components

## Usage

```bash
# Run all root-level tests
python3 -m pytest tests/root/

# Run specific test
python3 tests/root/test_integration_simple.py
```
""",
            "scripts/README.md": """# Project Scripts

Utility scripts for development, setup, and integration testing.

## Structure

- `setup/` - Environment setup and initialization scripts
- `integration/` - Integration testing and validation scripts

## Usage

```bash
# Setup development environment
./scripts/setup/start-dev.sh

# Run integration tests
python3 scripts/integration/bill_com_integration_test.py
```
""",
            "config/README.md": """# Configuration Files

Project configuration files and templates.

## Structure

- `secrets/` - Sensitive configuration files (gitignored)
- Root level - Non-sensitive configuration templates

## Security

Never commit files in the `secrets/` directory. Use the template files as examples.
""",
            "temp/README.md": """# Temporary Files

This directory contains temporary files generated during development and testing.

## Structure

- `logs/` - Application and server log files
- `test_results/` - Test execution results and traces

## Note

All contents of this directory are gitignored and should not be committed to version control.
""",
            "docs/README.md": """# Project Documentation

Comprehensive documentation for the Multi-Agent Custom Automation Engine.

## Structure

- `project/` - Project-level documentation and guides
- Backend-specific docs are in `backend/docs/`
- Frontend-specific docs are in `src/frontend/docs/` (if any)

## Key Documents

- `project/QUICK_START.md` - Getting started guide
- `project/Microsoft_Multi_Agent_Accelerator_README.md` - Microsoft accelerator documentation
"""
        }
        
        for readme_path, content in readme_contents.items():
            full_path = self.root_path / readme_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            self.log_action("CREATE", readme_path, "Documentation")
    
    def create_main_readme(self):
        """Create the main project README.md"""
        readme_content = """# Multi-Agent Custom Automation Engine (MACAE)

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
"""
        
        readme_path = self.root_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        self.log_action("CREATE", "README.md", "Main project documentation")
    
    def save_organization_log(self):
        """Save the organization log for review"""
        log_path = self.root_path / "temp" / "organization_log.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'w') as f:
            json.dump(self.organization_log, f, indent=2)
        
        print(f"\nOrganization log saved to: {log_path}")
    
    def organize(self):
        """Execute the complete organization process"""
        print("🚀 Starting root directory organization...")
        print("=" * 50)
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Execute organization steps
        self.create_directory_structure()
        self.organize_test_files()
        self.organize_log_files()
        self.organize_config_files()
        self.organize_scripts()
        self.organize_documentation()
        self.update_gitignore()
        self.create_readme_files()
        self.create_main_readme()
        
        # Save log
        self.save_organization_log()
        
        print("=" * 50)
        print("✅ Root directory organization complete!")
        print(f"📊 Total actions: {len(self.organization_log)}")
        print(f"📝 Log saved to: temp/organization_log.json")
        print("\n🔍 Review the changes and commit when ready:")
        print("   git add .")
        print("   git commit -m 'Organize root directory structure for GitHub readiness'")

def main():
    """Main execution function"""
    organizer = RootDirectoryOrganizer()
    organizer.organize()

if __name__ == "__main__":
    main()