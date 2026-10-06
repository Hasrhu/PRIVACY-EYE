# Privacy Eye — Scan Report REST API Specification

All endpoints are authenticated and require a valid JWT Bearer header or HttpOnly session cookie unless otherwise specified.

## Endpoints

### 1. Create Scan Report
**`POST /api/v1/reports`**

Creates a persistent forensic report snapshot from a live camera session.

**Request Body:**
```json
{
  "live_session_id": "sess_89f023b1",
  "save_face_capture": true,
  "representative_frame_base64": "data:image/jpeg;base64,...",
  "inference_result": {
    "assessment": "REAL_HUMAN_FACE",
    "category_label": "Real human face",
    "confidence": 88.5,
    "reliability": "HIGH",
    "input_quality": "GOOD",
    "blink_count": 3,
    "eye_status": "BOTH_EYES_VISIBLE",
    "presentation_attack": false
  }
}
```

**Response (`201 Created`):**
```json
{
  "id": "977b57ce-099d-42bc-a145-b89ceb10a9c9",
  "report_number": "PE-2026-6BC24B",
  "user_id": "ac2d5e70-7312-43be-90a7-5cc9c078ebe6",
  "live_session_id": "sess_89f023b1",
  "assessment": "REAL_HUMAN_FACE",
  "category_label": "Real human face",
  "confidence": 88.5,
  "reliability": "HIGH",
  "input_quality": "GOOD",
  "processing_location": "EDGE / LOCAL SERVER",
  "has_face_capture": true,
  "face_capture_available": true,
  "jpg_available": true,
  "pdf_available": true,
  "report_status": "COMPLETED",
  "model_name": "YuNet-DeepLearning-Face",
  "model_version": "v1.2.0",
  "preprocessing_version": "v1.2.0-spatial-fft",
  "fusion_version": "v1.4.0-guided-multisignal",
  "calibration_version": "v1.2.5-temperature",
  "target_face_id": "Face 1",
  "faces_detected_count": 1,
  "explanation": "All 3 live instructions verified: Authentic smile, 3 blinks, smooth rotation.",
  "why_reasons": [
    "Stable face detection and continuous 5-landmark tracking",
    "Clear ocular visibility with natural bilateral eye presence",
    "3 confirmed biological blinks observed",
    "Low replay and screen presentation risk (No Moiré pattern detected)"
  ],
  "signals": [
    {
      "id": "...",
      "signal_name": "BIOLOGICAL_BLINK",
      "signal_value": "3 blinks (TRACKING)",
      "signal_status": "PASS",
      "signal_explanation": "Biological involuntary eyelid closure pattern verified"
    }
  ],
  "tests": [
    {
      "id": "...",
      "test_name": "Face Detection",
      "status": "PASS",
      "score": 1.0,
      "message": "Target human face localized via YuNet neural detector"
    }
  ],
  "created_at": "2026-10-06T17:58:19.058Z",
  "updated_at": "2026-10-06T17:58:19.196Z"
}
```

---

### 2. List Reports
**`GET /api/v1/reports`**

Query parameters:
- `page` (default: 1)
- `per_page` (default: 20)
- `assessment` (optional filter: e.g. `REAL_HUMAN_FACE`, `POSSIBLE_REPLAY`)
- `search` (optional search by report number or title)

**Response (`200 OK`):**
```json
{
  "items": [ /* array of ScanReportResponse */ ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### 3. Retrieve Report by ID
**`GET /api/v1/reports/{id}`**

Path parameter: `id` (UUID or report number `PE-2026-XXXXXX`).
Strict ownership check enforced: returns `404` or `403` if not owned by authenticated user.

---

### 4. Download Representative Face Capture
**`GET /api/v1/reports/{id}/face`**

Streams the clean JPEG evidence frame. Returns `404` if report was saved under Privacy Mode (zero biometric storage).

---

### 5. Download Single-Page JPG Report Card
**`GET /api/v1/reports/{id}/jpg`**

Streams the high-resolution 1200x1600 JPG report graphic (`Content-Disposition: attachment`).

---

### 6. Download Official Multi-Page A4 PDF Dossier
**`GET /api/v1/reports/{id}/pdf`**

Streams the cryptographically styled A4 PDF document (`Content-Disposition: attachment`).

---

### 7. Delete Report
**`DELETE /api/v1/reports/{id}`**

Soft-deletes the database record, permanently unlinks face image, JPG, and PDF from storage, and records `report_deleted` in audit logs.
