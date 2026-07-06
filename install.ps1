# MP Mitra Automatic CLI Installer for Windows
# Run via: powershell -ExecutionPolicy Bypass -c "irm -useb https://raw.githubusercontent.com/harshith1432/mp-mitra/main/install.ps1 | iex"

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "         MP MITRA CLI AUTOMATIC INSTALLER         " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Prerequisite Checks
Write-Host "[*] Checking system prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pyVersion = & python --version 2>&1
    Write-Host "✅ Python Detected: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python 3.9+ is required but was not found on your system." -ForegroundColor Red
    Write-Host "Please install Python from https://python.org and add it to PATH before running this script." -ForegroundColor Yellow
    exit 1
}

# Check Node.js / NPM
try {
    $npmVersion = & npm --version 2>&1
    Write-Host "✅ Node.js / NPM Detected: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Node.js / NPM is required to compile the frontend dashboard." -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org before running this script." -ForegroundColor Yellow
    exit 1
}

# 2. Setup Directories
$InstallDir = "$env:USERPROFILE\.mpmitra"
$BinDir = "$InstallDir\bin"
Write-Host "[*] Creating installation directory at $InstallDir..." -ForegroundColor Yellow

if (Test-Path $InstallDir) {
    Write-Host "⚠️ Existing installation found. Removing old files..." -ForegroundColor DarkYellow
    Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $BinDir -Force | Out-Null

# 3. Download Source Code
Write-Host "[*] Downloading latest MP Mitra repository from GitHub..." -ForegroundColor Yellow
$ZipPath = "$InstallDir\repo.zip"
$RepoUrl = "https://github.com/harshith1432/mp-mitra/archive/refs/heads/main.zip"
Invoke-WebRequest -Uri $RepoUrl -OutFile $ZipPath

Write-Host "[*] Extracting source code..." -ForegroundColor Yellow
Expand-Archive -Path $ZipPath -DestinationPath $InstallDir -Force
Remove-Item -Path $ZipPath -Force

# Locate extracted directory
$ExtractedDir = Get-ChildItem -Path $InstallDir | Where-Object { $_.PSIsContainer -and $_.Name -like "mp-mitra-*" } | Select-Object -First 1
$RepoPath = $ExtractedDir.FullName

# 4. Configure Virtual Environment & Dependencies
Write-Host "[*] Setting up isolated Python virtual environment (venv)..." -ForegroundColor Yellow
& python -m venv "$InstallDir\venv"

Write-Host "[*] Installing Python backend dependencies (this may take a few minutes)..." -ForegroundColor Yellow
& "$InstallDir\venv\Scripts\pip.exe" install --upgrade pip | Out-Null
& "$InstallDir\venv\Scripts\pip.exe" install -r "$RepoPath\backend\requirements.txt"

# 5. Compile Frontend Dashboard
Write-Host "[*] Compiling React frontend dashboard static assets..." -ForegroundColor Yellow
Push-Location "$RepoPath\frontend"
try {
    & npm install
    & npm run build
} finally {
    Pop-Location
}

# Verify compiled frontend assets
$DistPath = "$RepoPath\frontend\dist"
if (-not (Test-Path $DistPath)) {
    Write-Error "❌ Error: frontend/dist directory does not exist after build."
    exit 1
}
if (-not (Test-Path "$DistPath\index.html")) {
    Write-Error "❌ Error: frontend/dist/index.html is missing."
    exit 1
}
if (-not (Test-Path "$DistPath\assets")) {
    Write-Error "❌ Error: frontend/dist/assets folder is missing."
    exit 1
}
Write-Host "✅ Verification: frontend/dist, index.html, and assets folder all exist!" -ForegroundColor Green

# 6. Create CLI Batch Wrapper Command
Write-Host "[*] Registering CLI wrapper command..." -ForegroundColor Yellow
$WrapperPath = "$BinDir\mpmitra.cmd"
$WrapperContent = @"
@echo off
"$InstallDir\venv\Scripts\python.exe" "$RepoPath\mpmitra.py" %*
"@
$WrapperContent | Out-File -FilePath $WrapperPath -Encoding ascii

# 7. Configure Environment PATH
Write-Host "[*] Registering mpmitra in System PATH..." -ForegroundColor Yellow
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    $NewUserPath = "$UserPath;$BinDir"
    [Environment]::SetEnvironmentVariable("PATH", $NewUserPath, "User")
    $env:PATH = "$env:PATH;$BinDir"
    Write-Host "✅ Path successfully configured!" -ForegroundColor Green
} else {
    Write-Host "✅ Path is already configured." -ForegroundColor Green
}

# 8. Success Banner
Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "🎉      INSTALLATION COMPLETED SUCCESSFULLY!      " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Please RESTART your terminal (Command Prompt, PowerShell, or Git Bash) for changes to take effect." -ForegroundColor Yellow
Write-Host "`nType the following commands to manage your deployment:" -ForegroundColor White
Write-Host "  mpmitra doctor   - Verify active ports, database and Firebase APIs" -ForegroundColor Cyan
Write-Host "  mpmitra start    - Launch background services and open dashboard" -ForegroundColor Cyan
Write-Host "  mpmitra status   - Check active process statuses" -ForegroundColor Cyan
Write-Host "  mpmitra stop     - Gracefully terminate background services" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green
