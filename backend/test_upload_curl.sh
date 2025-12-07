#!/bin/bash

# Simple curl-based test for file upload endpoint

echo "=========================================="
echo "Testing File Upload Endpoint with curl"
echo "=========================================="
echo ""

# Create test file
echo "Creating test invoice file..."
cat > /tmp/test_invoice.txt << 'EOF'
INVOICE

Invoice Number: INV-2024-001
Date: January 15, 2024

Bill To:
Acme Corporation
123 Business St
New York, NY 10001

Items:
1. Professional Services - $5,000.00
2. Consulting Hours (20 hrs @ $150/hr) - $3,000.00
3. Software License - $1,200.00

Subtotal: $9,200.00
Tax (8%): $736.00
Total: $9,936.00

Payment Due: February 15, 2024
EOF

echo "✓ Test file created at /tmp/test_invoice.txt"
echo ""

# Test the upload
echo "Uploading file to http://localhost:8000/api/v3/upload_file"
echo "------------------------------------------"
echo ""

curl -X POST \
  http://localhost:8000/api/v3/upload_file \
  -F "file=@/tmp/test_invoice.txt" \
  -H "Accept: application/json" \
  | python3 -m json.tool

echo ""
echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="

# Cleanup
rm /tmp/test_invoice.txt
