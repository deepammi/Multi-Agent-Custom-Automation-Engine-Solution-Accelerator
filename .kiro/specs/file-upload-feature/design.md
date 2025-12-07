# Design Document: File Upload Feature

## Overview

This feature adds file upload capability to the invoice processing workflow, allowing users to upload text files (.txt) and Microsoft Word documents (.doc, .docx) instead of manually pasting invoice text. The system will extract text content from uploaded files and populate the existing task description field for processing.

## Architecture

### High-Level Flow

```
User selects/drops file
    ↓
Frontend validates file type
    ↓
Frontend uploads file to backend
    ↓
Backend extracts text content
    ↓
Backend returns extracted text
    ↓
Frontend populates task description field
    ↓
User submits task (existing flow)
```

### Component Interaction

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  FileUpload     │────────▶│  HomePage        │────────▶│  API Client │
│  Component      │         │  (Parent)        │         │             │
└─────────────────┘         └──────────────────┘         └──────┬──────┘
                                                                  │
                                                                  │ HTTP POST
                                                                  │ multipart/form-data
                                                                  ▼
                                                          ┌──────────────┐
                                                          │  Backend API │
                                                          │  /upload_file│
                                                          └──────┬───────┘
                                                                  │
                                                                  ▼
                                                          ┌──────────────┐
                                                          │ File Parser  │
                                                          │ (.txt, .docx)│
                                                          └──────────────┘
```

## Components and Interfaces

### Frontend Components

#### 1. FileUploadZone Component
**Location**: `src/frontend/src/components/common/FileUploadZone.tsx`

**Responsibilities**:
- Render drag-and-drop upload area
- Handle file selection via click
- Validate file type and size on client side
- Display upload progress and status
- Call parent callback with extracted text

**Props**:
```typescript
interface FileUploadZoneProps {
    onFileContentExtracted: (content: string, filename: string) => void;
    onError: (error: string) => void;
    acceptedFileTypes?: string[];  // default: ['.txt', '.doc', '.docx']
    maxFileSizeMB?: number;        // default: 10
    disabled?: boolean;
}
```

**Key Methods**:
- `handleDrop(event: DragEvent)`: Handle file drop
- `handleFileSelect(event: ChangeEvent)`: Handle file selection
- `uploadFile(file: File)`: Upload file to backend
- `validateFile(file: File)`: Client-side validation

**UI States**:
- **Idle**: "Drag & drop invoice file here or click to browse"
- **Hover**: Highlighted drop zone with "Drop file here"
- **Uploading**: Progress spinner with "Uploading..."
- **Processing**: Spinner with "Extracting text from {filename}..."
- **Success**: Checkmark with "File uploaded: {filename}"
- **Error**: Error icon with error message

#### 2. HomePage Integration
**Location**: `src/frontend/src/pages/HomePage.tsx`

**Changes**:
- Add `FileUploadZone` component above task description textarea
- Handle `onFileContentExtracted` callback to populate textarea
- Handle `onError` callback to show error toast
- Maintain existing task submission flow

**New State**:
```typescript
const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
const [isFileUploaded, setIsFileUploaded] = useState(false);
```

### Backend Components

#### 1. File Upload Endpoint
**Location**: `backend/app/api/v3/routes.py`

**New Endpoint**:
```python
@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and extract text from invoice files.
    Supports: .txt, .doc, .docx
    """
```

**Request**:
- Method: POST
- Content-Type: multipart/form-data
- Body: file (binary)

**Response**:
```json
{
    "success": true,
    "filename": "invoice.docx",
    "content": "Extracted text content...",
    "file_size": 12345,
    "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
```

**Error Response**:
```json
{
    "success": false,
    "error": "Unsupported file type",
    "detail": "Only .txt, .doc, and .docx files are supported"
}
```

#### 2. File Parser Service
**Location**: `backend/app/services/file_parser_service.py`

**Responsibilities**:
- Extract text from .txt files
- Extract text from .docx files using python-docx
- Extract text from .doc files using textract
- Handle parsing errors gracefully
- Clean up temporary files

**Key Methods**:
```python
class FileParserService:
    @staticmethod
    async def extract_text(file: UploadFile) -> str:
        """Extract text from uploaded file based on type."""
        
    @staticmethod
    async def extract_text_from_txt(file_content: bytes) -> str:
        """Extract text from .txt file."""
        
    @staticmethod
    async def extract_text_from_docx(file_path: str) -> str:
        """Extract text from .docx file using python-docx."""
        
    @staticmethod
    async def extract_text_from_doc(file_path: str) -> str:
        """Extract text from .doc file using textract."""
```

## Data Models

### Frontend Types

```typescript
// src/frontend/src/models/fileUpload.tsx

export interface FileUploadResponse {
    success: boolean;
    filename: string;
    content: string;
    file_size: number;
    file_type: string;
    error?: string;
    detail?: string;
}

export interface FileUploadState {
    isUploading: boolean;
    isProcessing: boolean;
    uploadedFile: File | null;
    extractedContent: string | null;
    error: string | null;
}
```

### Backend Models

```python
# backend/app/models/file_upload.py

from pydantic import BaseModel
from typing import Optional

class FileUploadResponse(BaseModel):
    success: bool
    filename: str
    content: str
    file_size: int
    file_type: str
    error: Optional[str] = None
    detail: Optional[str] = None
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, the following properties can be identified:

**Core Properties**:
1. File upload and text extraction (Requirements 1.1-1.5, 2.1-2.5, 3.1-3.5)
2. User feedback during upload process (Requirements 4.1-4.5)

These properties are comprehensive and don't have redundancies since they cover different aspects of the feature.

### Correctness Properties

Property 1: File type acceptance
*For any* uploaded file, the system should accept .txt, .doc, and .docx files and reject all other file types with a clear error message
**Validates: Requirements 1.1, 1.3**

Property 2: Text extraction correctness
*For any* valid text file (.txt), the extracted content should match the original file content exactly, preserving line breaks and formatting
**Validates: Requirements 2.1, 2.2, 2.3**

Property 3: Word document extraction
*For any* valid Word document (.doc or .docx), the extracted text should contain all text content from the document, preserving paragraph structure
**Validates: Requirements 3.1, 3.2, 3.3**

Property 4: Task description population
*For any* successfully uploaded file, the extracted content should automatically populate the task description field
**Validates: Requirements 1.5, 2.3**

Property 5: Upload feedback consistency
*For any* file upload operation, the UI should display appropriate status messages during each phase: uploading, processing, success, or error
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

Property 6: Empty file handling
*For any* empty text file, the system should reject the upload and display an error message
**Validates: Requirements 2.4**

Property 7: File size validation
*For any* file exceeding 1MB, the system should display a file size warning
**Validates: Requirements 2.5, 4.5**

Property 8: Filename display
*For any* selected file, the system should display the filename and file size before upload begins
**Validates: Requirements 1.4**

## Error Handling

### Frontend Error Handling

**File Validation Errors**:
- Unsupported file type → "Unsupported file type. Please upload .txt, .doc, or .docx files."
- File too large → "File size exceeds 10MB limit. Please upload a smaller file."
- Empty file → "The selected file is empty. Please upload a file with content."
- No file selected → "Please select a file to upload."

**Upload Errors**:
- Network error → "Network error. Please check your connection and try again."
- Server error (5xx) → "Server error. Please try again later."
- Parsing error → "Failed to extract text from file. The file may be corrupted."
- Timeout → "Upload timed out. Please try again."

**Error Display**:
- Show errors in toast notifications with error intent
- Display inline error in upload zone
- Allow user to retry upload
- Clear error when new file is selected

### Backend Error Handling

**File Type Errors** (400 Bad Request):
```python
{
    "success": false,
    "error": "Unsupported file type",
    "detail": "Only .txt, .doc, and .docx files are supported"
}
```

**File Size Errors** (413 Payload Too Large):
```python
{
    "success": false,
    "error": "File too large",
    "detail": "Maximum file size is 10MB"
}
```

**Parsing Errors** (500 Internal Server Error):
```python
{
    "success": false,
    "error": "Text extraction failed",
    "detail": "Failed to extract text from document. File may be corrupted."
}
```

**Error Logging**:
- Log all errors with context (filename, file size, error details)
- Include stack traces for server errors
- Track error rates for monitoring

## Testing Strategy

### Unit Testing

**Frontend Unit Tests**:
1. Test `FileUploadZone` component with valid files
2. Test file type validation
3. Test file size validation
4. Test drag-and-drop functionality
5. Test error message display
6. Test callback invocation with extracted content

**Backend Unit Tests**:
1. Test text extraction from .txt files
2. Test text extraction from .docx files
3. Test text extraction from .doc files
4. Test file type validation
5. Test file size limits
6. Test error handling for corrupted files
7. Test temporary file cleanup

### Integration Testing

**End-to-End Upload Flow**:
1. User selects .txt file
2. Frontend uploads to backend
3. Backend extracts text
4. Frontend receives extracted text
5. Task description field is populated
6. User submits task

**Test Scenarios**:
- Upload .txt file with invoice text
- Upload .docx file with invoice text
- Upload .doc file with invoice text
- Upload file with special characters
- Upload file with tables (Word)
- Upload empty file (should fail)
- Upload unsupported file type (should fail)
- Upload file larger than 10MB (should fail)
- Upload file with network interruption
- Upload file with backend unavailable

### Manual Testing Checklist

- [ ] Upload .txt file via drag-and-drop
- [ ] Upload .txt file via click-to-browse
- [ ] Upload .docx file and verify text extraction
- [ ] Upload .doc file and verify text extraction
- [ ] Verify task description is populated with extracted text
- [ ] Upload empty file and verify error message
- [ ] Upload unsupported file type and verify error
- [ ] Upload large file and verify size warning
- [ ] Verify progress indicators during upload
- [ ] Verify success message after upload
- [ ] Edit extracted text before submitting task
- [ ] Submit task with uploaded content

## Implementation Notes

### File Upload Flow

1. **User selects file**:
   - Via drag-and-drop or file dialog
   - Frontend validates file type and size
   - Display filename and size

2. **Upload to backend**:
   - Use FormData with multipart/form-data
   - Show progress indicator
   - Handle upload errors

3. **Backend processing**:
   - Save file temporarily
   - Detect file type
   - Extract text using appropriate parser
   - Clean up temporary file
   - Return extracted text

4. **Frontend updates**:
   - Populate task description textarea
   - Show success message
   - Allow user to edit content
   - Enable task submission

### Libraries and Dependencies

**Frontend**:
```json
{
  "react-dropzone": "^14.2.3"
}
```

**Backend**:
```txt
python-docx==1.1.0
textract==1.6.5
python-magic==0.4.27
```

### File Type Detection

Use file extension for initial validation:
- `.txt` → Read as UTF-8 text
- `.docx` → Use python-docx library
- `.doc` → Use textract library

### Temporary File Handling

```python
import tempfile
import os

# Save uploaded file temporarily
with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
    content = await file.read()
    tmp_file.write(content)
    tmp_file_path = tmp_file.name

try:
    # Extract text
    extracted_text = await extract_text(tmp_file_path, file_extension)
finally:
    # Always clean up
    if os.path.exists(tmp_file_path):
        os.remove(tmp_file_path)
```

### UI/UX Considerations

**Upload Zone Design**:
- Dashed border with upload icon
- Clear instructions: "Drag & drop invoice file here or click to browse"
- Supported formats: ".txt, .doc, .docx"
- Visual feedback on hover (highlighted border)
- Compact design to fit above task description

**Integration with Existing UI**:
- Place upload zone above task description textarea
- Maintain existing textarea for editing
- Show uploaded filename above textarea
- Allow clearing uploaded content

### Performance Considerations

**File Size Limits**:
- Frontend: Validate before upload (10MB)
- Backend: FastAPI limit (10MB)
- Show progress for files > 1MB

**Text Extraction**:
- .txt files: Instant (read directly)
- .docx files: Fast (~100ms for typical invoice)
- .doc files: Slower (~500ms, requires textract)

**Optimization**:
- Stream file upload for large files
- Use async file operations
- Clean up temp files immediately after processing

## Security Considerations

### Input Validation

**Frontend Validation**:
- Check file extension before upload
- Validate file size (max 10MB)
- Sanitize filename for display

**Backend Validation**:
- Verify file type using magic bytes (not just extension)
- Enforce file size limit
- Validate extracted text length
- Sanitize extracted content

### File Handling

**Temporary Files**:
- Store in system temp directory
- Use unique filenames (UUID)
- Delete immediately after processing
- Handle cleanup on errors

**Content Security**:
- Limit extracted text length (max 100KB)
- Strip potentially malicious content
- Validate UTF-8 encoding
- Prevent path traversal attacks

## Deployment Considerations

### Environment Variables

```bash
# Maximum file upload size (bytes)
MAX_UPLOAD_SIZE=10485760  # 10MB

# Temporary file directory
TEMP_FILE_DIR=/tmp/invoice_uploads

# Supported file extensions
ALLOWED_EXTENSIONS=.txt,.doc,.docx
```

### Dependencies Installation

**Backend**:
```bash
pip install python-docx textract python-magic
```

**Frontend**:
```bash
npm install react-dropzone
```

### Platform-Specific Notes

**macOS/Linux**:
- textract requires system dependencies
- Install: `brew install antiword` (for .doc files)

**Windows**:
- textract may require additional setup
- Consider using only .txt and .docx for MVP

## Future Enhancements

### Phase 2 Features

1. **Content Preview**:
   - Show first 500 characters before populating textarea
   - "Show More" / "Show Less" toggle
   - Syntax highlighting for structured data

2. **Multiple File Support**:
   - Upload multiple files at once
   - Combine content from multiple files
   - Batch processing

3. **Advanced File Types**:
   - PDF support (using PyPDF2)
   - CSV support (using pandas)
   - Excel support (using openpyxl)
   - Image OCR (using tesseract)

4. **File Management**:
   - Store uploaded files in database
   - File history and re-use
   - Download original file

5. **Enhanced Security**:
   - Virus scanning
   - Content filtering
   - Rate limiting per user

## References

- [react-dropzone Documentation](https://react-dropzone.js.org/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [textract Documentation](https://textract.readthedocs.io/)
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
