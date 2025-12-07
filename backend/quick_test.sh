#!/bin/bash

echo "Testing File Upload Backend"
echo "=============================="
echo ""

# Make sure we're in the backend directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Test import
echo "1. Testing imports..."
python -c "from app.services.file_parser_service import FileParserService; print('✓ FileParserService imported successfully')"

if [ $? -ne 0 ]; then
    echo "❌ Import failed"
    exit 1
fi

echo ""
echo "2. Starting backend server..."
echo "   Run this in a separate terminal:"
echo "   cd backend && source venv/bin/activate && python -m app.main"
echo ""
echo "3. Then run the test:"
echo "   cd backend && source venv/bin/activate && python test_file_upload.py"
echo ""
echo "Or use the curl test:"
echo "   ./backend/test_upload_curl.sh"
echo ""
