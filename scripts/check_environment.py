"""
Privacy Eye — Hardware and Execution Environment Diagnostic Tool
Phase 1 Audit: Checks OS, Python, CUDA, GPU, VRAM, CPU, RAM, Disk, and Acceleration frameworks.
"""

import sys
import os
import platform
import shutil
import json
import subprocess


def inspect_environment():
    report = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
        },
        "python": {
            "version": sys.version.split()[0],
            "full": sys.version,
            "executable": sys.executable,
        },
        "hardware": {},
        "acceleration": {},
        "libraries": {},
    }

    # ── Disk Space ───────────────────────────────────────────────────────────
    try:
        total, used, free = shutil.disk_usage(".")
        report["hardware"]["disk"] = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
        }
    except Exception as e:
        report["hardware"]["disk"] = {"error": str(e)}

    # ── GPU & CUDA via nvidia-smi ────────────────────────────────────────────
    gpu_info = {"cuda_available": False, "gpu_count": 0, "devices": []}
    try:
        smi_out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version,utilization.gpu", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        )
        lines = [line.strip() for line in smi_out.strip().split("\n") if line.strip()]
        for idx, line in enumerate(lines):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpu_info["devices"].append({
                    "id": idx,
                    "name": parts[0],
                    "vram_total_mb": float(parts[1]),
                    "vram_free_mb": float(parts[2]),
                    "driver_version": parts[3],
                    "gpu_utilization_pct": float(parts[4]),
                })
        if gpu_info["devices"]:
            gpu_info["cuda_available"] = True
            gpu_info["gpu_count"] = len(gpu_info["devices"])
    except Exception as e:
        gpu_info["smi_error"] = str(e)

    report["hardware"]["gpu"] = gpu_info

    # ── CPU and RAM via Windows CIM/wmic fallback ────────────────────────────
    try:
        ps_cmd = "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name; (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB"
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], encoding="utf-8").strip().splitlines()
        if len(out) >= 2:
            report["hardware"]["cpu_name"] = out[0].strip()
            report["hardware"]["ram_total_gb"] = round(float(out[1].strip()), 2)
        elif len(out) == 1:
            report["hardware"]["cpu_name"] = out[0].strip()
    except Exception as e:
        report["hardware"]["cpu_ram_error"] = str(e)

    # ── Installed ML Libraries ───────────────────────────────────────────────
    libs = ["torch", "torchvision", "torchaudio", "cv2", "numpy", "pandas", "sklearn", "onnx", "onnxruntime", "mediapipe", "fastapi"]
    for lib in libs:
        try:
            mod = __import__(lib)
            report["libraries"][lib] = getattr(mod, "__version__", "installed")
        except ImportError:
            report["libraries"][lib] = "NOT_INSTALLED"

    # PyTorch specific checks
    if report["libraries"].get("torch") != "NOT_INSTALLED":
        import torch
        report["acceleration"]["torch_cuda_is_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            report["acceleration"]["torch_cuda_version"] = torch.version.cuda
            report["acceleration"]["torch_device_name"] = torch.cuda.get_device_name(0)
            report["acceleration"]["torch_device_capability"] = torch.cuda.get_device_capability(0)

    return report


if __name__ == "__main__":
    rep = inspect_environment()
    print("=" * 60)
    print("PRIVACY EYE — ML EXECUTION ENVIRONMENT AUDIT")
    print("=" * 60)
    print(f"OS: {rep['os']['platform']} ({rep['os']['architecture']})")
    print(f"Python: {rep['python']['version']}")
    print(f"CPU: {rep['hardware'].get('cpu_name', 'Unknown')}")
    print(f"RAM: {rep['hardware'].get('ram_total_gb', 'Unknown')} GB")
    disk = rep['hardware'].get('disk', {})
    print(f"Disk: {disk.get('free_gb', '?')} GB free / {disk.get('total_gb', '?')} GB total")
    gpu = rep['hardware'].get('gpu', {})
    if gpu.get('cuda_available'):
        for dev in gpu.get('devices', []):
            print(f"GPU [{dev['id']}]: {dev['name']} ({dev['vram_total_mb']} MB VRAM) - Driver {dev['driver_version']}")
    else:
        print("GPU: Dedicated NVIDIA GPU not detected or drivers inactive")
    print("\nLibraries Status:")
    for k, v in rep["libraries"].items():
        print(f"  {k:15}: {v}")
    print("=" * 60)
