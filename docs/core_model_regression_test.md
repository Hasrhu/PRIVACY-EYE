# Core Model Regression & Invariance Test Protocol

## 1. Absolute Invariance Requirement
The Privacy Eye Scan Report feature is strictly a **downstream audit and presentation consumer**. Under no circumstances may adding reports, PDF exports, JPG exports, database tables, or REST endpoints modify:
- Model architectures or model weights.
- Inference pipelines, algorithms, or thresholds.
- Preprocessing steps or frame normalization.
- Scoring formulas, confidence fusion, or blink calculation routines.

---

## 2. Test Verification Architecture

To guarantee zero regression and verify strict immutability, the test suite `backend/tests/test_core_model_immutability.py` was established and executed against the core inference engine (`LiveAuthenticityEngine`).

### 2.1 Fixed Deterministic Evaluation Inputs
The test suite defines a static corpus of simulated video frame arrays and biometric telemetry across multiple attack and bona fide scenarios:
1. **Live Human Sample**: Natural blinking, facial micro-movement, organic temporal consistency, low replay risk.
2. **Phone/Screen Replay Attack**: High screen reflection artifact, temporal periodicity, low 3D depth consistency.
3. **Synthetic / Deepfake Generation**: High manipulation indicator, synthetic boundary frequency anomalies.
4. **Poor Quality / Obscured Face**: Low illuminance, low resolution, face occlusion.

### 2.2 Baseline Output Record
Before implementing the report feature, the exact outputs were benchmarked:
- Output fields: `assessment`, `confidence`, `reliability`, `signals`, `metadata`.
- Exact numerical precision: All floating-point signal values preserved to 6 decimal places.

### 2.3 Post-Implementation Regression Assertion
The test runs all baseline fixtures through `LiveAuthenticityEngine.analyze_frame()` and asserts:
```python
assert baseline_result["assessment"] == new_result["assessment"]
assert baseline_result["confidence"] == pytest.approx(new_result["confidence"], abs=1e-6)
assert baseline_result["signals"] == new_result["signals"]
```

---

## 3. Automated Test Execution Results

```bash
$ pytest backend/tests/test_core_model_immutability.py -v
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-8.3.4
collected 5 items

backend/tests/test_core_model_immutability.py::test_core_model_weights_and_code_untouched PASSED [ 20%]
backend/tests/test_core_model_immutability.py::test_live_authenticity_engine_signature_invariant PASSED [ 40%]
backend/tests/test_core_model_immutability.py::test_inference_output_contract_identical PASSED [ 60%]
backend/tests/test_core_model_immutability.py::test_report_service_does_not_mutate_inference_object PASSED [ 80%]
backend/tests/test_core_model_immutability.py::test_downstream_reporting_zero_side_effects PASSED [100%]

============================== 5 passed in 0.42s ==============================
```

### 3.1 Verification Summary
- **Code Modifications to Core Model**: 0 lines changed in `backend/app/services/live_authenticity_engine.py` or any detection submodules.
- **Inference Results Change**: Exactly 0.00% difference.
- **Side Effects**: The `ScanReportService` only reads the structured inference dictionary and does not mutate it.
