# Implementation Plan

- [ ] 1. Set up backend file upload infrastructure
  - Install required Python libraries (python-docx, python-magic)
  - Create FileParserService for text extraction
  - Add file upload endpoint to FastAPI
  - _Requirements: 1.1, 1.3, 2.1, 3.1_

- [x] 1.1 Install backend dependencies
  - Add python-docx to requirements.txt
  - Add python-magic to requirements.txt (for file type detection)
  - Install dependencies in virtual environment
  - _Requirements: 2.1, 3.1_

- [x] 1.2 Create FileParserService
  - Create backend/app/services/file_parser_service.py
  - Implement extract_text() method for routing by file type
  - Implement extract_text_from_txt() for .txt files
  - Implement extract_text_from_docx() for .docx files
  - Add error handling for corrupted files
  - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

- [x] 1.3 Create file upload endpoint
  - Add POST /api/v3/upload_file endpoint in routes.py
  - Accept multipart/form-data with file upload
  - Validate file type (.txt, .doc, .docx only)
  - Enforce 10MB file size limit
  - Call FileParserService to extract text
  - Return extracted text in JSON response
  - Clean up temporary files after processing
  - _Requirements: 1.3, 1.5, 2.3, 3.3, 4.4_

- [ ] 2. Create frontend file upload component
  - Install react-dropzone library
  - Create FileUploadZone component
  - Implement drag-and-drop functionality
  - Add file selection dialog
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2.1 Install frontend dependencies
  - Add react-dropzone to package.json
  - Install dependencies with npm install
  - _Requirements: 1.1, 1.2_

- [x] 2.2 Create FileUploadZone component
  - Create src/frontend/src/components/common/FileUploadZone.tsx
  - Implement drag-and-drop UI with react-dropzone
  - Add file selection dialog on click
  - Display upload zone with instructions
  - Show accepted file types (.txt, .doc, .docx)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2.3 Implement file validation and upload
  - Validate file type on client side
  - Validate file size (max 10MB)
  - Display filename and file size after selection
  - Upload file to backend endpoint
  - Handle upload progress
  - _Requirements: 1.4, 2.5, 4.1_

- [x] 2.4 Add upload status feedback
  - Show "Uploading..." spinner during upload
  - Show "Processing file..." during text extraction
  - Show success message with filename
  - Show error messages for failures
  - Display file size warnings
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Integrate file upload with HomePage
  - Add FileUploadZone to HomePage above task description
  - Handle extracted text callback
  - Populate task description textarea with extracted content
  - _Requirements: 1.5, 2.3_

- [x] 3.1 Add FileUploadZone to HomePage
  - Import FileUploadZone component
  - Place component above task description textarea
  - Add state for uploaded file tracking
  - Style component to fit existing UI
  - _Requirements: 1.5_

- [x] 3.2 Handle file content extraction
  - Implement onFileContentExtracted callback
  - Populate task description textarea with extracted text
  - Show success toast notification
  - Handle error callback and display error toast
  - _Requirements: 1.5, 2.3, 4.3, 4.4_

- [ ] 4. Testing and validation
  - Test .txt file upload and extraction
  - Test .docx file upload and extraction
  - Test error scenarios (empty file, wrong type, too large)
  - Verify task submission with uploaded content
  - _Requirements: All_

- [ ] 4.1 Test text file upload
  - Create sample .txt invoice file
  - Upload via drag-and-drop
  - Upload via file dialog
  - Verify text extraction preserves formatting
  - Verify task description is populated
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4.2 Test Word document upload
  - Create sample .docx invoice file
  - Upload and verify text extraction
  - Test with tables in document
  - Verify paragraph structure is preserved
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 4.3 Test error handling
  - Upload empty file (should show error)
  - Upload unsupported file type (should reject)
  - Upload file > 10MB (should show warning)
  - Test with corrupted file
  - Verify error messages are clear
  - _Requirements: 2.4, 4.4, 4.5_

- [ ] 4.4 End-to-end workflow test
  - Upload invoice file
  - Verify content in task description
  - Edit content if needed
  - Submit task
  - Verify invoice processing works normally
  - _Requirements: All_

- [ ] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
