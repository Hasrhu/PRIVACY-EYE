"""
File service — secure temporary file handling.
All uploaded files are processed in memory or temp storage and immediately deleted.
Privacy principle: No Storage. No Spying. Only Detection.
"""
import os
import aiofiles
import tempfile
import uuid
from pathlib import Path
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class FileService:
    def __init__(self):
        self.temp_dir = Path(settings.TEMP_UPLOAD_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def save_temp(self, content: bytes, suffix: str = "") -> Path:
        """Save bytes to a temp file. Caller MUST call delete_temp() after use."""
        fname = f"{uuid.uuid4().hex}{suffix}"
        fpath = self.temp_dir / fname
        async with aiofiles.open(fpath, "wb") as f:
            await f.write(content)
        logger.debug("Temp file created", path=str(fpath), size=len(content))
        return fpath

    def delete_temp(self, path: Path) -> None:
        """Securely delete a temporary file."""
        try:
            if path.exists():
                path.unlink()
                logger.debug("Temp file deleted", path=str(path))
        except Exception as e:
            logger.error("Failed to delete temp file", path=str(path), error=str(e))

    def get_extension(self, mime_type: str) -> str:
        mapping = {
            "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
            "video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
            "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav",
            "audio/ogg": ".ogg", "audio/flac": ".flac",
        }
        return mapping.get(mime_type, "")


file_service = FileService()
