"""Test script for file upload endpoint."""
import asyncio
import httpx
import os

# Test files content
SAMPLE_TXT_INVOICE = """INVOICE

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
"""

SAMPLE_DOCX_INVOICE = """INVOICE

Invoice #: INV-2024-002
Date: January 20, 2024

From:
Tech Solutions Inc.
456 Tech Ave
San Francisco, CA 94102

To:
Global Enterprises
789 Corporate Blvd
Chicago, IL 60601

Description                    Quantity    Price       Total
Web Development                1           $8,500.00   $8,500.00
Database Setup                 1           $2,500.00   $2,500.00
Monthly Maintenance            3           $500.00     $1,500.00

Subtotal: $12,500.00
Tax: $1,000.00
Total Due: $13,500.00
"""


async def test_file_upload():
    """Test the file upload endpoint with sample files."""
    
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Testing File Upload Endpoint")
    print("=" * 60)
    print()
    
    # Create test files
    test_files_dir = "test_files"
    os.makedirs(test_files_dir, exist_ok=True)
    
    txt_file_path = os.path.join(test_files_dir, "sample_invoice.txt")
    with open(txt_file_path, "w") as f:
        f.write(SAMPLE_TXT_INVOICE)
    
    print(f"✓ Created test file: {txt_file_path}")
    print()
    
    async with httpx.AsyncClient() as client:
        # Test 1: Upload .txt file
        print("Test 1: Uploading .txt file")
        print("-" * 60)
        
        try:
            with open(txt_file_path, "rb") as f:
                files = {"file": ("sample_invoice.txt", f, "text/plain")}
                response = await client.post(
                    f"{base_url}/api/v3/upload_file",
                    files=files,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS!")
                print(f"   Filename: {result['filename']}")
                print(f"   File Size: {result['file_size']} bytes")
                print(f"   Content Type: {result['file_type']}")
                print(f"   Extracted Text Length: {len(result['content'])} characters")
                print()
                print("   First 200 characters of extracted text:")
                print(f"   {result['content'][:200]}...")
                print()
            else:
                print(f"❌ FAILED with status {response.status_code}")
                print(f"   Error: {response.text}")
                print()
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print()
        
        # Test 2: Upload empty file (should fail)
        print("Test 2: Uploading empty file (should fail)")
        print("-" * 60)
        
        try:
            empty_file_path = os.path.join(test_files_dir, "empty.txt")
            with open(empty_file_path, "w") as f:
                f.write("")
            
            with open(empty_file_path, "rb") as f:
                files = {"file": ("empty.txt", f, "text/plain")}
                response = await client.post(
                    f"{base_url}/api/v3/upload_file",
                    files=files,
                    timeout=30.0
                )
            
            if response.status_code == 400:
                print(f"✅ Correctly rejected empty file")
                print(f"   Error message: {response.json()['detail']}")
                print()
            else:
                print(f"❌ Should have rejected empty file but got status {response.status_code}")
                print()
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print()
        
        # Test 3: Upload unsupported file type (should fail)
        print("Test 3: Uploading unsupported file type (should fail)")
        print("-" * 60)
        
        try:
            pdf_file_path = os.path.join(test_files_dir, "test.pdf")
            with open(pdf_file_path, "w") as f:
                f.write("fake pdf content")
            
            with open(pdf_file_path, "rb") as f:
                files = {"file": ("test.pdf", f, "application/pdf")}
                response = await client.post(
                    f"{base_url}/api/v3/upload_file",
                    files=files,
                    timeout=30.0
                )
            
            if response.status_code == 400:
                print(f"✅ Correctly rejected unsupported file type")
                print(f"   Error message: {response.json()['detail']}")
                print()
            else:
                print(f"❌ Should have rejected PDF but got status {response.status_code}")
                print()
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            print()
    
    # Cleanup
    print("Cleaning up test files...")
    import shutil
    if os.path.exists(test_files_dir):
        shutil.rmtree(test_files_dir)
    print("✓ Cleanup complete")
    print()
    
    print("=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print()
    print("Make sure the backend server is running on http://localhost:8000")
    print("Run: cd backend && python -m app.main")
    print()
    input("Press Enter when ready to test...")
    print()
    
    asyncio.run(test_file_upload())
