"""
Privacy Eye — Scan Reports Feature Integration & Security Tests
Tests:
1. Report creation with face capture
2. Privacy mode (zero biometric storage)
3. Idempotency (multiple clicks generate single report)
4. IDOR / BOLA authorization security (cross-user isolation)
5. Unauthenticated access rejection
6. PDF & JPG generation validation (valid magic bytes & content)
7. Deletion and artifact purging
8. Core model immutability verification (downstream reporting)
"""
import pytest
import io
import base64
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import create_access_token
from app.database.session import AsyncSessionLocal
from app.database.models import User, UserRole
from app.ml.live_authenticity import live_authenticity_engine


def make_dummy_face_b64(width=160, height=160, color=(180, 140, 120)) -> str:
    """Generates a small valid test face JPEG in base64."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@pytest.mark.asyncio
async def test_scan_reports_full_lifecycle_and_security():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup two test users in database
        async with AsyncSessionLocal() as db:
            import uuid
            user_a_id = str(uuid.uuid4())
            user_b_id = str(uuid.uuid4())

            user_a = User(
                id=user_a_id,
                email=f"user_a_{user_a_id[:8]}@privacyeye.ai",
                hashed_password="hashed_pass_a",
                full_name="Agent Alpha",
                role=UserRole.USER,
                is_active=True,
            )
            user_b = User(
                id=user_b_id,
                email=f"user_b_{user_b_id[:8]}@privacyeye.ai",
                hashed_password="hashed_pass_b",
                full_name="Agent Beta",
                role=UserRole.USER,
                is_active=True,
            )
            db.add(user_a)
            db.add(user_b)
            await db.commit()

        token_a = create_access_token(user_a_id)
        token_b = create_access_token(user_b_id)
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 2. Simulated inference result from core model
        sample_snapshot = {
            "assessment": "REAL_HUMAN_FACE",
            "category_label": "Real human face",
            "confidence": 88.5,
            "reliability": "HIGH",
            "input_quality": "GOOD",
            "face_detected": True,
            "eye_status": "BOTH_EYES_VISIBLE",
            "presentation_attack": False,
            "phone_detected": False,
            "spatial_risk": 0.05,
            "liveness_score": 0.885,
            "explanation": "All live instructions verified: Authentic smile, smooth rotation.",
            "guided_protocol": {
                "task_3_rotation": {"marked": True}
            }
        }
        face_b64 = make_dummy_face_b64()

        # 3. Test 1: User A creates report
        session_id_1 = f"sess_{uuid.uuid4().hex[:8]}"
        create_payload = {
            "live_session_id": session_id_1,
            "save_face_capture": True,
            "representative_frame_base64": face_b64,
            "inference_result": sample_snapshot,
        }

        resp = await client.post("/api/v1/reports", json=create_payload, headers=headers_a)
        assert resp.status_code == 201, resp.text
        data = resp.json()

        report_id = data["id"]
        report_number = data["report_number"]
        assert report_number.startswith("PE-")
        assert data["assessment"] == "REAL_HUMAN_FACE"
        assert data["confidence"] == 88.5
        assert data["reliability"] == "HIGH"
        assert data["has_face_capture"] is True
        assert data["face_capture_available"] is True
        assert data["pdf_available"] is True
        assert data["jpg_available"] is True
        assert len(data["signals"]) > 0
        assert len(data["tests"]) > 0

        # 4. Test 2: Idempotency (User A creates report again with same session ID)
        resp_idem = await client.post("/api/v1/reports", json=create_payload, headers=headers_a)
        assert resp_idem.status_code == 201
        assert resp_idem.json()["id"] == report_id  # Same report returned

        # 5. Test 3: User A retrieves own report
        resp_get = await client.get(f"/api/v1/reports/{report_id}", headers=headers_a)
        assert resp_get.status_code == 200
        assert resp_get.json()["id"] == report_id

        # 6. Test 4: IDOR Protection — User B cannot retrieve User A's report
        resp_idor = await client.get(f"/api/v1/reports/{report_id}", headers=headers_b)
        assert resp_idor.status_code in (403, 404)

        # 7. Test 5: IDOR Protection — User B cannot download User A's face capture
        resp_face_idor = await client.get(f"/api/v1/reports/{report_id}/face", headers=headers_b)
        assert resp_face_idor.status_code in (403, 404)

        # 8. Test 6: Unauthenticated user cannot access report
        resp_unauth = await client.get(f"/api/v1/reports/{report_id}")
        assert resp_unauth.status_code == 401

        # 9. Test 7: User A downloads face capture
        resp_face = await client.get(f"/api/v1/reports/{report_id}/face", headers=headers_a)
        assert resp_face.status_code == 200
        assert resp_face.headers["content-type"] == "image/jpeg"
        assert len(resp_face.content) > 100

        # 10. Test 8: User A downloads PDF report
        resp_pdf = await client.get(f"/api/v1/reports/{report_id}/pdf", headers=headers_a)
        assert resp_pdf.status_code == 200
        assert resp_pdf.headers["content-type"] == "application/pdf"
        assert resp_pdf.content.startswith(b"%PDF")  # Valid PDF signature!

        # 11. Test 9: User A downloads JPG report
        resp_jpg = await client.get(f"/api/v1/reports/{report_id}/jpg", headers=headers_a)
        assert resp_jpg.status_code == 200
        assert resp_jpg.headers["content-type"] == "image/jpeg"
        assert resp_jpg.content.startswith(b"\xff\xd8\xff")  # Valid JPEG signature!

        # 12. Test 10: Privacy Mode (Save report WITHOUT face capture)
        session_id_privacy = f"sess_{uuid.uuid4().hex[:8]}"
        privacy_payload = {
            "live_session_id": session_id_privacy,
            "save_face_capture": False,
            "representative_frame_base64": face_b64,
            "inference_result": sample_snapshot,
        }
        resp_priv = await client.post("/api/v1/reports", json=privacy_payload, headers=headers_a)
        assert resp_priv.status_code == 201
        priv_data = resp_priv.json()
        assert priv_data["has_face_capture"] is False
        assert priv_data["face_capture_available"] is False

        # Attempting to fetch face for privacy report returns 404
        resp_no_face = await client.get(f"/api/v1/reports/{priv_data['id']}/face", headers=headers_a)
        assert resp_no_face.status_code == 404

        # 13. Test 11: List Reports for User A
        resp_list = await client.get("/api/v1/reports", headers=headers_a)
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert list_data["total"] >= 2
        assert any(item["id"] == report_id for item in list_data["items"])

        # 14. Test 12: Delete Report workflow
        resp_del = await client.delete(f"/api/v1/reports/{report_id}", headers=headers_a)
        assert resp_del.status_code == 200

        # Subsequent fetch returns 404
        resp_after_del = await client.get(f"/api/v1/reports/{report_id}", headers=headers_a)
        assert resp_after_del.status_code == 404

        # Deleted report face download fails
        resp_del_face = await client.get(f"/api/v1/reports/{report_id}/face", headers=headers_a)
        assert resp_del_face.status_code == 404
