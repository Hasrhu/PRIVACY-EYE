# Privacy Eye — ML Execution & Training Environment Audit
**Phase 1 Deliverable**  
**Audit Timestamp**: 2026-09-28T23:57:00+05:30  
**Machine Architecture**: Windows 11 x64 (Build 26200)

---

## 1. Executive Hardware & Platform Summary

```
┌────────────────────────────────────────────────────────────────────────┐
│                      HARDWARE AUDIT OVERVIEW                           │
├───────────────────────┬────────────────────────────────────────────────┤
│ Operating System      │ Windows 11 Home/Pro (Build 26200, 64-bit AMD64)│
│ Processor (CPU)       │ Intel(R) Core(TM) i5-10200H @ 2.40GHz          │
│ Cores / Threads       │ 4 Physical Cores / 8 Logical Processors        │
│ System Memory (RAM)   │ 16.0 GB DDR4-2933                              │
│ Dedicated GPU (dGPU)  │ NVIDIA GeForce RTX 3050 Laptop GPU             │
│ VRAM Capacity         │ 4096 MiB (4.0 GB GDDR6)                        │
│ NVIDIA Driver Version │ 610.74 (WDDM 3.2)                              │
│ CUDA Driver Support   │ CUDA 13.3                                      │
│ Integrated GPU (iGPU) │ Intel(R) UHD Graphics (Comet Lake GT2)         │
│ Storage & Disk Space  │ 207.54 GB Available / 475.61 GB Total SSD      │
│ Base Python Version   │ Python 3.14.4 (tags/v3.14.4) [AMD64]          │
│ OpenCV Version        │ OpenCV 5.0.0 (High-performance SIMD active)    │
│ NumPy Version         │ NumPy 2.5.3                                    │
└───────────────────────┴────────────────────────────────────────────────┘
```

---

## 2. Hardware Resource Constraints & Engineering Strategy

### A. GPU Memory (4.0 GB VRAM) Budgets
The dedicated NVIDIA GeForce RTX 3050 Laptop GPU has **4,096 MB VRAM**:
1. **Model Training Constraints**:
   - **Spatial Backbones (ResNet-50 / EfficientNet-B4)**: Maximum batch size of $8$ at FP16 with mixed precision (`torch.cuda.amp`).
   - **Spatio-Temporal Sequence Models (16-frame 3D CNNs / VideoMAE)**: Requires gradient checkpointing and a batch size of $1$ to $2$ to avoid CUDA Out-Of-Memory (OOM).
   - **Large Vision Foundations (ViT-L / Swin-B / UniversalFakeDetect CLIP-L/14)**: Training or fine-tuning from scratch locally is **prohibited** due to VRAM limits; inference or feature extraction with frozen weights in `eval()` mode is permitted using batch size 1.
2. **Inference & Live Production Constraints**:
   - Optimized **ONNX Runtime (DirectML / CUDA EP)** models require $\le 350\text{ MB}$ VRAM for lightweight spatial networks and $\approx 180\text{ MB}$ system RAM for CPU fallback.
   - Real-time 30 FPS webcam processing is fully supported at native $720\text{p} \rightarrow 256\times 256$ face ROI.

### B. Python Compatibility Advisory
- The host system runs **Python 3.14.4**.
- While core data processing libraries (`numpy 2.5.3`, `cv2 5.0.0`) are active, major deep learning frameworks (e.g. `torch`, `torchvision`, `mediapipe`, `onnxruntime`) currently publish official pre-compiled CUDA wheels primarily for **Python 3.10 – 3.12**.
- **Remediation Plan**:
  1. For pure inference and forensic execution, OpenCV DNN + YuNet + ONNX engine runs directly on Python 3.14.
  2. For heavy PyTorch CUDA model training experiments, a isolated Python 3.11 virtual environment (`.venv-py311`) will be created via `uv` or Python 3.11 standalone runtime.

### C. Disk Space (207 GB Free) Allocation
- **Datasets Buffer**: Allocated up to $60\text{ GB}$ for face-crop HDF5 / Parquet shards (avoiding storage of raw duplicate uncompressed video frames).
- **Checkpoints Storage**: $15\text{ GB}$ for storing top validation and generalization weights (`best_validation.pt`, `best_generalization.pt`).
- **Operating Margin**: $\ge 120\text{ GB}$ preserved for OS paging and scratch disk.

---

## 3. Recommended Execution Modes

| Operational Mode | Target Hardware | Precision | Expected Latency | Purpose |
|---|---|---|---|---|
| **Live Camera Inference** | CPU (AVX2) + dGPU (DirectML) | FP16 / INT8 | 18 ms – 35 ms | Real-time 30 FPS client webcam feed |
| **Forensic Deep Scan** | dGPU (CUDA 13.3) | FP16 | 120 ms – 250 ms | High-confidence multi-signal fusion |
| **Model Fine-Tuning** | dGPU (CUDA AMP) | Mixed FP16 | 2.5 – 6.0 hrs/epoch | Transfer learning on held-out splits |
| **Fallback Graceful Mode** | Intel CPU (AVX-512/AVX2) | FP32 | 45 ms – 70 ms | Server failover if GPU crashes |
