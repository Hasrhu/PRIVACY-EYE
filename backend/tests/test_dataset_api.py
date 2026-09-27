"""
Privacy Eye — Test Suite for Dataset REST API Endpoints
Compatible with FastAPI TestClient and async engine lifespan.
"""

import unittest
import base64
import numpy as np
import cv2
from starlette.testclient import TestClient

from app.main import app


class TestDatasetAPI(unittest.TestCase):

    def test_quality_gate_endpoint(self):
        with TestClient(app) as client:
            # Create a small valid test image in base64
            img = np.full((150, 150, 3), 120, dtype=np.uint8)
            cv2.circle(img, (75, 75), 40, (220, 220, 220), -1)
            cv2.rectangle(img, (20, 20), (130, 130), (50, 50, 200), 2)
            _, buffer = cv2.imencode(".jpg", img)
            b64_str = base64.b64encode(buffer).decode("utf-8")

            response = client.post(
                "/api/v1/dataset/quality-gate",
                json={"image_base64": b64_str},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("passed", data)
            self.assertIn("overall_quality_score", data)
            self.assertIn("quality_label", data)
            self.assertIn("rejection_reasons", data)

    def test_dataset_record_create_and_stats(self):
        with TestClient(app) as client:
            sample_id = f"test_sample_cat_a_{np.random.randint(10000, 99999)}"
            payload = {
                "sample_id": sample_id,
                "category": "CATEGORY_A_GENUINE",
                "source_dataset": "InternalConsent",
                "license_terms": "InternalConsent-v1",
                "subject_id": "subj_999",
                "true_label": "real",
                "split": "train",
                "consent_verified": True,
            }
            res = client.post("/api/v1/dataset/records", json=payload)
            self.assertEqual(res.status_code, 201)
            data = res.json()
            self.assertEqual(data["sample_id"], sample_id)

            # Query stats
            stats_res = client.get("/api/v1/dataset/stats")
            self.assertEqual(stats_res.status_code, 200)
            stats = stats_res.json()
            self.assertGreaterEqual(stats["total_samples"], 1)
            self.assertIn("CATEGORY_A_GENUINE", stats["category_counts"])

    def test_failure_case_logging_and_review(self):
        with TestClient(app) as client:
            payload = {
                "model_version": "v2.0",
                "input_type": "image",
                "device": "mac_hd",
                "resolution": "720p",
                "environment": "office",
                "true_label": "real",
                "prediction": "POSSIBLE REPLAY",
                "confidence": 0.82,
                "reason": "Screen reflection in glasses mistaken for display replay",
            }
            res = client.post("/api/v1/dataset/failure-cases", json=payload)
            self.assertEqual(res.status_code, 201)
            data = res.json()
            failure_id = data["failure_id"]

            # Human Review endpoint
            rev_res = client.post(
                f"/api/v1/dataset/failure-cases/{failure_id}/review?reviewer_id=lead_investigator&approve_for_retraining=true"
            )
            self.assertEqual(rev_res.status_code, 200)
            rev_data = rev_res.json()
            self.assertTrue(rev_data["is_verified_by_human"])
            self.assertEqual(rev_data["reviewed_by"], "lead_investigator")
            self.assertTrue(rev_data["added_to_training_set"])


if __name__ == "__main__":
    unittest.main()
