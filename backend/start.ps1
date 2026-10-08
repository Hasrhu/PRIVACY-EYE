# Privacy Eye — Safe Backend Startup Script
Write-Host "🛡️ Starting Privacy Eye Backend..." -ForegroundColor Cyan

# 1. Ensure .env exists safely without overwriting
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

# 2. Database Protection & Automated Backup
if (Test-Path "privacyeye.db") {
    $backupDir = "backups"
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    }
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "$backupDir/privacyeye_backup_$timestamp.db"
    Copy-Item "privacyeye.db" $backupPath -Force
    Copy-Item "privacyeye.db" "$backupDir/privacyeye_safeguard_latest.db" -Force
    Write-Host "✅ Database safeguarded: Backup created at $backupPath" -ForegroundColor Green
}

# 3. Environment Activation
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
} elseif (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "Virtual environment not detected. Using python on PATH." -ForegroundColor Yellow
}

# 4. Start Uvicorn Server
Write-Host "🚀 Launching Privacy Eye API on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
