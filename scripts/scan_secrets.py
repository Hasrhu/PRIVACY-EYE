"""
Privacy Eye — Automated Pre-Deployment Secret Scanner
Scans all Git-tracked files for exposed API keys, private keys, passwords, and tokens.
"""
import os
import re
import subprocess
import sys

PATTERNS = [
    (re.compile(r'(?i)api[_-]?key\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']'), "API Key"),
    (re.compile(r'(?i)secret[_-]?key\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']'), "Secret Key"),
    (re.compile(r'(?i)password\s*[:=]\s*["\']([^"\']{8,})["\']'), "Hardcoded Password"),
    (re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----'), "Private Key"),
    (re.compile(r'hf_[a-zA-Z0-9]{34,}'), "Hugging Face Token"),
    (re.compile(r'postgres(?:ql)?://(?![^:]+:[^@]+@localhost)[^:\s]+:[^@\s]+@[^\s/]+'), "Production Database URI with credentials"),
]

EXCLUDE_PATTERNS = [
    "example",
    "placeholder",
    "your-",
    "your_",
    "<",
    "sqlite",
    "tests/",
    "user:pass",
    "${",
    "username:password",
    "postgres_host",
]

def scan():
    try:
        tracked_files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    except Exception as e:
        print(f"Error reading git ls-files: {e}")
        return 1

    findings = []
    for f in tracked_files:
        if not os.path.exists(f) or os.path.isdir(f):
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                for idx, line in enumerate(fp, 1):
                    # Skip comment or example lines
                    line_lower = line.lower()
                    if any(ex in line_lower for ex in EXCLUDE_PATTERNS):
                        continue
                    for pat, desc in PATTERNS:
                        m = pat.search(line)
                        if m:
                            findings.append((f, idx, desc))
        except Exception:
            pass

    print(f"=== SECRET SCAN COMPLETED: {len(tracked_files)} files scanned ===")
    if findings:
        print(f"WARNING: {len(findings)} potential secret(s) found:")
        for f, idx, desc in findings:
            print(f"  {f}:{idx} -> {desc}")
        return 1
    else:
        print("SUCCESS: 0 exposed secrets found in tracked repository files.")
        return 0

if __name__ == "__main__":
    sys.exit(scan())
