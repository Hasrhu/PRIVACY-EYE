# Privacy Eye — Scan Report Database Schema

## Relational Architecture

The Scan Report subsystem introduces three relational tables in the primary database, integrated with existing `users` and `audit_logs` tables.

### 1. `scan_reports`

Stores the primary audit record and snapshot of inference results for each verified live scan.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | No | Primary Key (UUIDv4) |
| `report_number` | VARCHAR(50) | No | Unique non-sequential reference code (e.g. `PE-2026-6BC24B`), indexed |
| `user_id` | VARCHAR(36) | No | Foreign Key (`users.id` ON DELETE CASCADE), indexed |
| `live_session_id` | VARCHAR(100) | No | Client session nonce for idempotency and correlation, indexed |
| `assessment` | VARCHAR(100) | No | Final assessment label (e.g. `REAL_HUMAN_FACE`, `POSSIBLE_REPLAY`) |
| `category_label` | VARCHAR(200) | Yes | Human-readable category title shown on UI |
| `confidence` | FLOAT | No | Calibrated confidence score (0.0 – 100.0) |
| `reliability` | VARCHAR(50) | No | Reliability category (`HIGH`, `MEDIUM`, `LOW`) |
| `input_quality` | VARCHAR(50) | No | Stream quality rating (`GOOD`, `ACCEPTABLE`, `POOR`) |
| `processing_location`| VARCHAR(100) | No | Inference execution location (`EDGE / LOCAL SERVER`) |
| `has_face_capture` | BOOLEAN | No | True if face image stored, False if Zero-Biometric mode |
| `face_capture_storage_key` | VARCHAR(500) | Yes | Private filesystem or bucket storage key for face JPEG |
| `jpg_report_storage_key` | VARCHAR(500) | Yes | Private storage key for rendered JPG report card |
| `pdf_report_storage_key` | VARCHAR(500) | Yes | Private storage key for rendered PDF evidence dossier |
| `report_status` | VARCHAR(50) | No | Lifecycle status (`GENERATING`, `COMPLETED`, `FAILED`, `PARTIAL`) |
| `model_name` | VARCHAR(100) | No | Core model identifier (`YuNet-DeepLearning-Face`) |
| `model_version` | VARCHAR(50) | No | Model weights version (`v1.2.0`) |
| `preprocessing_version` | VARCHAR(50) | No | Preprocessing pipeline version (`v1.2.0-spatial-fft`) |
| `fusion_version` | VARCHAR(50) | No | Multi-signal fusion engine version (`v1.4.0-guided-multisignal`) |
| `calibration_version` | VARCHAR(50) | No | Confidence calibration profile (`v1.2.5-temperature`) |
| `target_face_id` | VARCHAR(50) | Yes | Tracked target face identifier (`Face 1`) |
| `faces_detected_count` | INTEGER | No | Total simultaneous faces observed in frame (default: 1) |
| `explanation` | TEXT | Yes | Primary explainability rationale |
| `why_reasons` | JSON | Yes | Array of structured reasons with green checkmarks |
| `raw_snapshot` | JSON | Yes | Exact full JSON dictionary emitted by core inference model |
| `deleted_at` | DATETIME | Yes | Soft-delete timestamp |
| `created_at` | DATETIME | No | UTC timestamp of report creation |
| `updated_at` | DATETIME | No | UTC timestamp of last update |

### 2. `scan_report_signals`

Forensic biometric signals extracted during the analysis session.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | No | Primary Key (UUIDv4) |
| `report_id` | VARCHAR(36) | No | Foreign Key (`scan_reports.id` ON DELETE CASCADE), indexed |
| `signal_name` | VARCHAR(100) | No | Signal key (e.g. `EYE_VISIBILITY`, `BIOLOGICAL_BLINK`, `LIVENESS_CONFIDENCE`) |
| `signal_value` | VARCHAR(200) | No | Value or metric (e.g. `BOTH_EYES_VISIBLE`, `3 blinks`, `88.5%`) |
| `signal_status` | VARCHAR(50) | No | Signal outcome status (`PASS`, `WARNING`, `FAIL`, `INFO`) |
| `signal_explanation` | TEXT | Yes | Technical description of the forensic indicator |
| `created_at` | DATETIME | No | UTC creation timestamp |

### 3. `scan_report_tests`

Discrete verification tests performed during the live authenticity protocol.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | No | Primary Key (UUIDv4) |
| `report_id` | VARCHAR(36) | No | Foreign Key (`scan_reports.id` ON DELETE CASCADE), indexed |
| `test_name` | VARCHAR(100) | No | Name of verification test (e.g. `Face Detection`, `Blink Detection`, `Presentation Attack / Screen Detection`) |
| `status` | VARCHAR(50) | No | Outcome status (`PASS`, `FAIL`, `WARNING`, `NOT_AVAILABLE`, `NOT_APPLICABLE`) |
| `score` | FLOAT | Yes | Fractional metric (0.0 – 1.0) if applicable |
| `message` | TEXT | Yes | Specific observation finding |
| `timestamp` | DATETIME | No | UTC execution timestamp |
