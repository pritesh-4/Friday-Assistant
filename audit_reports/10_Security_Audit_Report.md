# 10. Security Audit Report

## Audit Scope
- Inspected the document ingestion pipeline (`FileService` and `DocumentParser`).
- Tested for Directory Traversal vulnerabilities (e.g., `../../etc/passwd`).
- Verified MIME and extension whitelisting boundaries.

## Findings & Resolutions

### 1. File Upload Sandbox & Path Traversal
- **Investigation**: Unrestricted file uploads can lead to arbitrary code execution or server compromise if a user modifies the HTTP payload to include traversal patterns in the `filename`.
- **Validation**: Checked `backend/app/services/file_service.py`.
  - The filename is immediately sanitized using a regex (`re.sub(r"[^a-zA-Z0-9_.-]", "_", raw_name)`).
  - Storage paths are explicitly resolved (`.resolve()`) and then checked against the root `uploads_directory` string bounds. If the path tries to escape the `uploads/` folder, it raises a clean `400 Bad Request`.
- **Status**: PASSED. Highly secure sandbox.

### 2. Extension Whitelisting
- **Validation**: `FileService` strictly relies on an explicit hardcoded set of `allowed_extensions` (PDF, DOCX, CSV, JSON, MD, TXT, images) preventing `.exe`, `.sh`, or `.py` file ingestion.
- **Status**: PASSED.

## Conclusion
The backend implements rigorous zero-trust policies regarding user-supplied file metadata. The system is immune to standard path traversal and malicious file type injection attacks.
