# Root Level Tests

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
