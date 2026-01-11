# Backend Tests

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
