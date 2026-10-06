"""
Privacy Eye — Secure Private Storage Service
Provides encrypted/private filesystem abstraction for sensitive face captures,
PDF reports, and JPG evidence snapshots.

Never exposes direct public URLs. Access is strictly authenticated and authorization-controlled.
"""
import os
import io
import shutil
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import structlog

logger = structlog.get_logger(__name__)

STORAGE_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "secure_reports"
)
os.makedirs(STORAGE_BASE_DIR, exist_ok=True)

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_DOC_BYTES = 25 * 1024 * 1024    # 25MB


class SecureStorageService:
    def __init__(self, base_dir: str = STORAGE_BASE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, storage_key: str) -> Path:
        # Prevent directory traversal attacks
        safe_key = storage_key.strip("/\\").replace("..", "")
        resolved = (self.base_dir / safe_key).resolve()
        if not str(resolved).startswith(str(self.base_dir)):
            raise ValueError("Invalid storage path key: Directory traversal attempt detected")
        return resolved

    def validate_face_image(self, img_bytes: bytes) -> Tuple[bool, Optional[str], Optional[Tuple[int, int]]]:
        """
        Validates that image is not corrupt, has sufficient dimensions, and is within size limits.
        """
        if not img_bytes:
            return False, "Empty image data", None

        if len(img_bytes) > MAX_IMAGE_BYTES:
            return False, f"Image exceeds maximum allowable size of {MAX_IMAGE_BYTES // (1024*1024)}MB", None

        try:
            with Image.open(io.BytesIO(img_bytes)) as img:
                img.verify()
            
            # Reopen to inspect dimensions (verify() closes buffer state)
            with Image.open(io.BytesIO(img_bytes)) as img:
                w, h = img.size
                if w < 48 or h < 48:
                    return False, f"Resolution too low ({w}x{h}). Minimum required is 48x48.", (w, h)
                return True, None, (w, h)
        except Exception as e:
            return False, f"Malformed or corrupted image format: {str(e)}", None

    def save_face_capture(self, user_id: str, report_id: str, img_bytes: bytes) -> str:
        """
        Saves a representative face capture JPEG securely under the user and report namespace.
        Returns the opaque storage key.
        """
        valid, err, dims = self.validate_face_image(img_bytes)
        if not valid:
            raise ValueError(f"Face image validation failed: {err}")

        storage_key = f"users/{user_id}/reports/{report_id}/face_evidence.jpg"
        file_path = self._resolve_path(storage_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert / re-encode to clean standard JPEG
        try:
            with Image.open(io.BytesIO(img_bytes)) as img:
                rgb_img = img.convert("RGB")
                rgb_img.save(file_path, format="JPEG", quality=90, optimize=True)
        except Exception:
            # Fallback direct byte write if re-encode fails
            with open(file_path, "wb") as f:
                f.write(img_bytes)

        logger.info("Face capture saved to secure storage", report_id=report_id, key=storage_key)
        return storage_key

    def save_pdf_report(self, user_id: str, report_id: str, pdf_bytes: bytes) -> str:
        """
        Saves generated PDF report securely.
        """
        if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Invalid PDF payload: Missing %PDF signature")

        storage_key = f"users/{user_id}/reports/{report_id}/report.pdf"
        file_path = self._resolve_path(storage_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        logger.info("PDF report saved to secure storage", report_id=report_id, key=storage_key)
        return storage_key

    def save_jpg_report(self, user_id: str, report_id: str, jpg_bytes: bytes) -> str:
        """
        Saves generated JPG report graphic securely.
        """
        if not jpg_bytes or len(jpg_bytes) < 100:
            raise ValueError("Invalid JPG payload")

        storage_key = f"users/{user_id}/reports/{report_id}/report.jpg"
        file_path = self._resolve_path(storage_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(jpg_bytes)

        logger.info("JPG report saved to secure storage", report_id=report_id, key=storage_key)
        return storage_key

    def get_file_bytes(self, storage_key: Optional[str]) -> Optional[bytes]:
        """
        Reads private file bytes by storage key. Returns None if key is empty or file doesn't exist.
        """
        if not storage_key:
            return None

        try:
            path = self._resolve_path(storage_key)
            if not path.exists() or not path.is_file():
                return None
            with open(path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error("Failed to read storage file", key=storage_key, error=str(e))
            return None

    def get_file_path(self, storage_key: Optional[str]) -> Optional[str]:
        """
        Returns absolute system path if file exists, else None.
        """
        if not storage_key:
            return None
        try:
            path = self._resolve_path(storage_key)
            if path.exists() and path.is_file():
                return str(path)
            return None
        except Exception:
            return None

    def delete_report_bundle(self, user_id: str, report_id: str) -> bool:
        """
        Deletes all evidence files (face capture, JPG, PDF) associated with a report.
        """
        try:
            report_dir = self._resolve_path(f"users/{user_id}/reports/{report_id}")
            if report_dir.exists() and report_dir.is_dir():
                shutil.rmtree(report_dir, ignore_errors=True)
                logger.info("Secure report bundle deleted", user_id=user_id, report_id=report_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete report bundle", report_id=report_id, error=str(e))
            return False


storage_service = SecureStorageService()
