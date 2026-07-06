# MP Mitra — Frontend Deploy Automation Script
# ============================================
# Builds the React frontend with the configured Render backend URL
# and deploys it to Firebase Hosting.

Write-Host "🚀 Starting MP Mitra Frontend Deploy Pipeline..." -ForegroundColor Cyan

# Check if npm is installed
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Error "Error: Node.js/npm is not installed or not in your PATH. Please install Node.js first."
    exit 1
}

# Check if firebase CLI is installed
if (-not (Get-Command "firebase" -ErrorAction SilentlyContinue)) {
    Write-Error "Error: Firebase CLI is not installed. Please install it by running: npm install -g firebase-tools"
    exit 1
}

# 1. Build the React application
Write-Host "`n📦 Step 1: Compiling React Frontend (Vite)..." -ForegroundColor Yellow
Set-Location -Path "frontend"
npm install
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error: Frontend compilation failed."
    exit 1
}

# 2. Deploy to Firebase hosting
Write-Host "`n☁️ Step 2: Deploying to Firebase Hosting..." -ForegroundColor Yellow
Set-Location -Path ".."
firebase deploy --only hosting

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error: Firebase deployment failed. Make sure you are logged in using: firebase login"
    exit 1
}

Write-Host "`n🎉 Success! Your frontend is live on Firebase and connected to the Render backend." -ForegroundColor Green
