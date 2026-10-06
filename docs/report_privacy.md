# Privacy Eye — Scan Report Privacy Architecture & Data Governance

## Privacy Principles

Biometric facial imagery constitutes sensitive personal data. The Privacy Eye Scan Report feature is built from the ground up to respect user sovereignty, GDPR/CCPA guidelines, and privacy-preserving design.

### 1. Zero Silent Image Storage
- No video frames or camera feeds are ever saved automatically or continuously in the background.
- At the conclusion of a scan, the user is presented with a clear consent dialog before any data is written to disk.

### 2. Privacy Mode Selection
Users are granted full granular control over report persistence:
- **Mode A: Full Evidence Audit** (`SAVE_REPORT=true, SAVE_FACE_CAPTURE=true`): Persists report metadata and a single representative evidence face frame.
- **Mode B: Zero-Biometric Audit** (`SAVE_REPORT=true, SAVE_FACE_CAPTURE=false`): Persists mathematical test scores, signals, and explainability without retaining any raw facial imagery. The evidence slot displays a cryptographic *Zero-Biometric Policy Enforced* notice.
- **Mode C: Ephemeral Discard** (`SAVE_REPORT=false`): Completely discards session data and frames; nothing is stored.

### 3. Representative Frame Timing
- Privacy Eye does NOT record video streams.
- Only a single stable representative frame captured at the end of the analysis is saved when explicit consent is provided.

### 4. Non-Identifying Storage Namespaces
- No personally identifying filenames (e.g. `JohnDoe_face.jpg`) are used.
- Storage keys follow opaque UUID paths:
  `users/{user_id}/reports/{report_id}/face_evidence.jpg`
- No public web URLs exist. All downloads require authenticated session authorization.

### 5. Configurable Retention & Purging
- When a user deletes a report, the database record is soft-deleted, and all associated physical artifacts (face JPEG, report PDF, report JPG) are permanently purged from the storage filesystem.
