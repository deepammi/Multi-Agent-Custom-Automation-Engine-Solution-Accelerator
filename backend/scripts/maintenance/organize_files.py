#!/usr/bin/env python3
"""
Script to organize backend files into proper directory structure
"""
import os
import shutil
import glob
from pathlib import Path

def organize_backend_files():
    """Organize backend files into proper directory structure"""
    
    # Define file patterns and their destinations
    file_moves = {
        # Test files
        'tests/unit/': [
            'test_*_simple.py',
            'test_*_config.py',
            'test_*_validation.py',
            'test_minimal_*.py',
            'test_llm_*.py',
            'test_env_*.py',
            'test_gemini_simple.py',
            'test_checkpointer.py',
            'test_graph_*.py',
        ],
        'tests/integration/': [
            'test_*_integration*.py',
            'test_*_workflow*.py',
            'test_ap_crm_*.py',
            'test_planner_*.py',
            'test_multi_agent_*.py',
            'test_frontend_*.py',
            'test_websocket_*.py',
            'test_mcp_*.py',
            'test_bill_com_*.py',
            'test_salesforce_*.py',
            'test_gmail_*.py',
            'test_email_*.py',
            'test_crm_*.py',
            'test_accounts_payable_*.py',
            'test_invoice_*.py',
            'test_analysis_*.py',
        ],
        'tests/e2e/': [
            'test_comprehensive_*.py',
            'test_end_to_end_*.py',
            'test_complete_*.py',
            'test_real_*.py',
            'test_po_*.py',
            'test_cli_*.py',
            'test_final_*.py',
            'test_task*_*.py',
        ],
        'tests/property/': [
            'test_*_properties.py',
            'test_agent_coordinator_properties.py',
        ],
        
        # Debug scripts
        'scripts/debug/': [
            'debug_*.py',
            'diagnose_*.py',
            'check_*.py',
            'show_*.py',
            'verify_*.py',
            'validate_*.py',
            'trace_*.py',
        ],
        
        # Setup scripts
        'scripts/setup/': [
            'setup_*.py',
            'start_*.py',
            'stop_*.py',
            'restart_*.py',
            'gmail_auth.py',
            'update_*.py',
            'run_*.py',
            'example_*.py',
        ],
        
        # Shell scripts
        'scripts/deployment/': [
            '*.sh',
        ],
        
        # Test results and traces
        'temp/test_results/': [
            '*_results_*.json',
            '*.log',
        ],
        'temp/traces/': [
            'trace_*.txt',
            '*.trace',
            'ComprehensiveTestTrace.txt',
        ],
    }
    
    # Move files based on patterns
    for dest_dir, patterns in file_moves.items():
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        for pattern in patterns:
            files = glob.glob(pattern)
            for file in files:
                if os.path.isfile(file):
                    try:
                        shutil.move(file, dest_path / os.path.basename(file))
                        print(f"Moved {file} -> {dest_dir}")
                    except Exception as e:
                        print(f"Error moving {file}: {e}")
    
    # Create README files for each directory
    readme_contents = {
        'tests/README.md': """# Backend Tests

## Directory Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests between components
- `e2e/` - End-to-end workflow tests
- `property/` - Property-based tests
- `fixtures/` - Test fixtures and utilities

## Running Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test category
python3 -m pytest tests/unit/
python3 -m pytest tests/integration/
python3 -m pytest tests/e2e/
```
""",
        
        'scripts/README.md': """# Backend Scripts

## Directory Structure

- `setup/` - Environment setup and initialization scripts
- `debug/` - Debug utilities and diagnostic tools
- `deployment/` - Deployment and system management scripts
- `maintenance/` - Maintenance and cleanup utilities

## Usage

Most scripts can be run directly with Python 3:
```bash
python3 scripts/setup/setup_environment.py
```
""",
        
        'temp/README.md': """# Temporary Files

This directory contains temporary files generated during development and testing.

- `test_results/` - JSON results from test runs
- `traces/` - Debug traces and logs

**Note**: Files in this directory are not committed to version control.
""",
        
        'docs/README.md': """# Backend Documentation

This directory contains backend-specific documentation.

## Contents

- API documentation
- Architecture diagrams
- Development guides
- Deployment instructions
""",
    }
    
    # Create README files
    for readme_path, content in readme_contents.items():
        with open(readme_path, 'w') as f:
            f.write(content)
        print(f"Created {readme_path}")

if __name__ == "__main__":
    organize_backend_files()
    print("File organization complete!")