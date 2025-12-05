#!/bin/bash

# Get the latest extraction and display it nicely
echo "=== Latest Invoice Extractions ==="
echo ""

# Get all extractions
response=$(curl -s http://localhost:8000/api/v3/extractions)

# Extract plan_ids and display them
echo "$response" | python3 -c "
import sys
import json

data = json.load(sys.stdin)
extractions = data.get('extractions', [])

if not extractions:
    print('No extractions found')
    sys.exit(0)

print(f'Found {len(extractions)} extraction(s):\n')

for i, ext in enumerate(extractions[:5], 1):  # Show last 5
    plan_id = ext.get('plan_id', 'unknown')
    vendor = ext.get('invoice_data', {}).get('vendor_name', 'N/A')
    invoice_num = ext.get('invoice_data', {}).get('invoice_number', 'N/A')
    approved_at = ext.get('approved_at', 'N/A')
    success = ext.get('success', False)
    errors = len(ext.get('validation_errors', []))
    
    print(f'{i}. Plan ID: {plan_id}')
    print(f'   Vendor: {vendor}')
    print(f'   Invoice #: {invoice_num}')
    print(f'   Success: {success} (Errors: {errors})')
    print(f'   Approved: {approved_at}')
    print(f'   URL: http://localhost:8000/api/v3/extraction/{plan_id}/json')
    print()
"

echo ""
echo "=== To get a specific extraction as JSON ==="
echo "curl http://localhost:8000/api/v3/extraction/{plan_id}/json | jq"
echo ""
echo "=== To get a specific extraction as CSV ==="
echo "curl http://localhost:8000/api/v3/extraction/{plan_id}/csv"
