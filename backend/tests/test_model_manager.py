"""
Unit tests for ModelManager and Health/Readiness endpoints.
"""
try:
    import pytest
except ImportError:
    pytest = None
from pathlib import Path
from app.services.model_manager import (
    ModelManager,
    MODEL_PRESENT,
    MODEL_READY,
    MODEL_MISSING,
)
from app.core.config import settings


def test_model_manager_manifest_loading():
    mm = ModelManager()
    manifest = mm.manifest
    assert "models" in manifest
    assert len(manifest["models"]) >= 1

    yunet = mm.get_manifest_entry("face_detection_yunet")
    assert yunet is not None
    assert yunet["filename"] == "face_detection_yunet.onnx"
    assert yunet["required_at_runtime"] is True


def test_model_manager_sanitized_status():
    mm = ModelManager()
    status = mm.get_model_status()
    assert "ml_engine_status" in status
    assert "device" in status
    assert "models" in status
    assert "token" not in str(status).lower()
    assert "secret" not in str(status).lower()


def test_model_manager_sha256_verification(tmp_path: Path):
    mm = ModelManager(cache_dir=str(tmp_path))
    test_file = tmp_path / "sample.bin"
    test_file.write_bytes(b"privacy-eye-integrity-test")

    import hashlib
    expected_sha = hashlib.sha256(b"privacy-eye-integrity-test").hexdigest()

    assert mm.verify_model(test_file, expected_sha) is True
    assert mm.verify_model(test_file, "wrong_hash") is False


if __name__ == "__main__":
    import tempfile
    test_model_manager_manifest_loading()
    test_model_manager_sanitized_status()
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_model_manager_sha256_verification(Path(tmp_dir))
    print("All ModelManager tests executed successfully!")

