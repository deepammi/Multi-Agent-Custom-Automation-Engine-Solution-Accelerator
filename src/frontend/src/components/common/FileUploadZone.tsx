import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Button,
  Spinner,
  Text,
  Caption1,
} from '@fluentui/react-components';
import {
  ArrowUpload24Regular,
  Checkmark24Regular,
  Dismiss24Regular,
  Document24Regular,
} from '@fluentui/react-icons';
import styles from '../../styles/FileUploadZone.module.css';

interface FileUploadZoneProps {
  onFileContentExtracted: (content: string, filename: string) => void;
  onError: (error: string) => void;
  acceptedFileTypes?: string[];
  maxFileSizeMB?: number;
  disabled?: boolean;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFileContentExtracted,
  onError,
  acceptedFileTypes = ['.txt', '.doc', '.docx'],
  maxFileSizeMB = 10,
  disabled = false,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const maxFileSizeBytes = maxFileSizeMB * 1024 * 1024;

  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true);
    setIsProcessing(false);
    setError(null);
    setUploadSuccess(false);
    setUploadedFileName(file.name);

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', file);

      // Get API URL from environment
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      // Upload to backend
      const response = await fetch(`${apiUrl}/api/v3/upload_file`, {
        method: 'POST',
        body: formData,
      });

      setIsUploading(false);
      setIsProcessing(true);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload file');
      }

      const result = await response.json();

      setIsProcessing(false);
      setUploadSuccess(true);
      setUploadedFileName(result.filename);

      // Call parent callback with extracted content
      onFileContentExtracted(result.content, result.filename);

      // Reset success state after 3 seconds
      setTimeout(() => {
        setUploadSuccess(false);
        setUploadedFileName(null);
      }, 3000);

    } catch (err: any) {
      setIsUploading(false);
      setIsProcessing(false);
      setUploadSuccess(false);
      const errorMessage = err.message || 'Failed to upload file';
      setError(errorMessage);
      onError(errorMessage);
    }
  }, [onFileContentExtracted, onError]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      uploadFile(file);
    }
  }, [uploadFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: maxFileSizeBytes,
    multiple: false,
    disabled: disabled || isUploading || isProcessing,
    onDropRejected: (fileRejections) => {
      const rejection = fileRejections[0];
      if (rejection) {
        const errorCode = rejection.errors[0]?.code;
        let errorMessage = 'File rejected';
        
        if (errorCode === 'file-too-large') {
          errorMessage = `File size exceeds ${maxFileSizeMB}MB limit`;
        } else if (errorCode === 'file-invalid-type') {
          errorMessage = `Unsupported file type. Please upload ${acceptedFileTypes.join(', ')} files`;
        } else {
          errorMessage = rejection.errors[0]?.message || 'File rejected';
        }
        
        setError(errorMessage);
        onError(errorMessage);
      }
    },
  });

  return (
    <div className={styles.container}>
      <div
        {...getRootProps()}
        className={`${styles.dropzone} ${
          isDragActive ? styles.dropzoneActive : ''
        } ${disabled ? styles.dropzoneDisabled : ''} ${
          error ? styles.dropzoneError : ''
        } ${uploadSuccess ? styles.dropzoneSuccess : ''}`}
      >
        <input {...getInputProps()} />

        {/* Uploading State */}
        {isUploading && (
          <div className={styles.statusContainer}>
            <Spinner size="small" />
            <Text className={styles.statusText}>Uploading {uploadedFileName}...</Text>
          </div>
        )}

        {/* Processing State */}
        {isProcessing && (
          <div className={styles.statusContainer}>
            <Spinner size="small" />
            <Text className={styles.statusText}>
              Extracting text from {uploadedFileName}...
            </Text>
          </div>
        )}

        {/* Success State */}
        {uploadSuccess && !isUploading && !isProcessing && (
          <div className={styles.statusContainer}>
            <Checkmark24Regular className={styles.successIcon} />
            <Text className={styles.statusText}>
              File uploaded: {uploadedFileName}
            </Text>
          </div>
        )}

        {/* Error State */}
        {error && !isUploading && !isProcessing && !uploadSuccess && (
          <div className={styles.statusContainer}>
            <Dismiss24Regular className={styles.errorIcon} />
            <Text className={styles.errorText}>{error}</Text>
            <Button
              appearance="subtle"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                setError(null);
              }}
            >
              Try Again
            </Button>
          </div>
        )}

        {/* Idle State */}
        {!isUploading && !isProcessing && !uploadSuccess && !error && (
          <div className={styles.idleContainer}>
            {isDragActive ? (
              <>
                <ArrowUpload24Regular className={styles.uploadIcon} />
                <Text className={styles.idleText}>Drop file here</Text>
              </>
            ) : (
              <>
                <Document24Regular className={styles.documentIcon} />
                <Text className={styles.idleText}>
                  Drag & drop invoice file here or click to browse
                </Text>
                <Caption1 className={styles.supportedFormats}>
                  Supported formats: {acceptedFileTypes.join(', ')} (max {maxFileSizeMB}MB)
                </Caption1>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUploadZone;
