# Privacy Eye — Scan Report Security Architecture & Threat Model

## 1. Overview
The Privacy Eye Scan Report feature adheres to a defense-in-depth security model to safeguard biometrics, forensic audit trails, and user privacy against unauthorized access, tampering, IDOR/BOLA attacks, and data leakage.

---

## 2. Authentication & Authorization Principles

### 2.1 Server-Enforced User Ownership (Anti-IDOR / Anti-BOLA)
- Client-provided `user_id` values in request bodies or query parameters are **never trusted**.
- Every report lookup, generation request, file download (`/face`, `/jpg`, `/pdf`), and deletion request extracts the authenticated user identity strictly from the cryptographically verified JWT bearer session (`get_current_user`).
- Access verification check:
  ```python
  if report.user_id != current_user.id and current_user.role != "admin":
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND, # Obscure existence against enumeration
          detail="Report not found"
      )
  ```
- Cross-tenant or unauthorized requests return `404 Not Found` rather than `403 Forbidden` to prevent resource enumeration.

### 2.2 Role-Based Access Control (RBAC)
- Standard users can only view, download, and delete reports they own.
- Administrative endpoints (`/api/v1/reports/admin/all`) require `current_user.role == "admin"`.
- All admin access events to user reports or face captures are logged in the `AuditLog` table with `action="admin_report_inspection"`.

---

## 3. Storage Security & Path Traversal Prevention

### 3.1 Non-Public Private Object Storage
- Biometric face frames and generated documents (PDF/JPG) are never placed in public buckets or static web roots.
- All files are stored under isolated per-user, per-report storage paths:
  `storage/secure_reports/users/{user_id}/reports/{report_id}/`
- Files are only accessible via authenticated, ownership-validated streaming endpoints.

### 3.2 Path Traversal Defense
- File retrieval utilizes strict path resolution checks:
  ```python
  resolved_path = file_path.resolve()
  if not resolved_path.is_relative_to(self.base_dir.resolve()):
      raise SecurityException("Path traversal attempt detected")
  ```

### 3.3 Non-Guessable Identifiers
- User-facing Report ID: `PE-YYYY-XXXXXX` (cryptographically random hex segment).
- Internal database identifier: UUIDv4.
- Sequential IDs are never used as authorization tokens.

---

## 4. Input Validation & Defense Against Malformed Payloads

### 4.1 Image Header & Integrity Verification
- Captured base64 frames are decoded and verified using PIL (`Image.open(io.BytesIO(data))`).
- Dimensions and color profiles are inspected; corrupted or zero-byte buffers are rejected with HTTP 422 before storage.
- File size thresholds are strictly enforced (maximum 10MB per face frame).

### 4.2 Idempotency Enforced on Server
- Duplicate clicks on "Save Report" with identical `(user_id, live_session_id)` return the existing report record rather than creating redundant database rows or generating duplicate files.

---

## 5. Audit Logging

Security-critical events are recorded to the persistent `AuditLog` table:
- `report_created`: Report record, face frame, and documents created.
- `report_viewed`: User or admin inspected report forensic details.
- `report_downloaded`: JPG or PDF downloaded (specifying format).
- `report_deleted`: User requested permanent deletion.
- `face_capture_accessed`: Raw biometric image downloaded or reviewed.

Log entries store timestamps, actor user IDs, target report IDs, client IP addresses, and user-agent strings. **Raw biometric image payloads and confidential tokens are never written to audit logs.**

---

## 6. Deletion & Orphan Purging
- When a user deletes a report (`DELETE /api/v1/reports/{id}`), the backend immediately:
  1. Deletes the face capture file (`face.jpg`).
  2. Deletes the JPG summary card (`report.jpg`).
  3. Deletes the multi-page PDF dossier (`report.pdf`).
  4. Removes the directory tree for that report ID.
  5. Cascades deletions for signals and test rows in PostgreSQL.
  6. Soft-deletes or purges the `ScanReport` row.
  7. Emits an audit event `report_deleted`.
