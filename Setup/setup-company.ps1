# Setup script for company environment on Windows
# Run as: powershell -ExecutionPolicy Bypass -File setup-company.ps1

Write-Host "🏢 Setting up COMPANY workflow environment..." -ForegroundColor Green

# Security check
Write-Host "`n⚠️  SECURITY REMINDER:" -ForegroundColor Red
Write-Host "This is the COMPANY setup. DO NOT copy workflow.py here!" -ForegroundColor Yellow
Write-Host "Only workflow-company.py should be used at company.`n" -ForegroundColor Yellow

$continue = Read-Host "Continue with company setup? (y/n)"
if ($continue -ne 'y') {
    exit 0
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 3 not found!" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host "→ Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install requests pyyaml

# Create directory structure
Write-Host "→ Creating directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "conversion-tools" | Out-Null
New-Item -ItemType Directory -Force -Path "conversion-tools\scripts" | Out-Null
New-Item -ItemType Directory -Force -Path "conversion-tools\scripts\config_profiles" | Out-Null

# Check for workflow-company.py
if (-not (Test-Path "conversion-tools\workflow-company.py")) {
    Write-Host "⚠️  workflow-company.py not found!" -ForegroundColor Yellow
    Write-Host "Please copy workflow-company.py to conversion-tools\" -ForegroundColor Yellow
    
    $download = Read-Host "Download from GitHub? (y/n)"
    if ($download -eq 'y') {
        # Replace with your actual GitHub URL
        $url = "https://raw.githubusercontent.com/YOUR_REPO/main/workflow-company.py"
        Write-Host "Downloading workflow-company.py..."
        Invoke-WebRequest -Uri $url -OutFile "conversion-tools\workflow-company.py"
    }
}

# Security check - ensure workflow.py is NOT present
if (Test-Path "conversion-tools\workflow.py") {
    Write-Host "❌ SECURITY WARNING: workflow.py found!" -ForegroundColor Red
    Write-Host "This file should NOT be at company!" -ForegroundColor Red
    $delete = Read-Host "Delete it? (y/n)"
    if ($delete -eq 'y') {
        Remove-Item "conversion-tools\workflow.py" -Force
        Write-Host "✓ Removed workflow.py" -ForegroundColor Green
    }
}

# Initialize
Write-Host "→ Initializing company workflow..." -ForegroundColor Yellow
python conversion-tools\workflow-company.py init

Write-Host "`n✅ Company setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Update .workflow-config-company.yaml with server details" -ForegroundColor White
Write-Host "2. Get company_profile.yaml from your team" -ForegroundColor White
Write-Host "3. Test connection:" -ForegroundColor White
Write-Host "   python conversion-tools\workflow-company.py check-server" -ForegroundColor Gray
Write-Host "4. Test emergency procedures:" -ForegroundColor White
Write-Host "   python conversion-tools\workflow-company.py emergency" -ForegroundColor Gray

# Create convenient shortcuts
Write-Host "`n→ Creating convenient shortcuts..." -ForegroundColor Yellow

@"
@echo off
python conversion-tools\workflow-company.py %*
"@ | Out-File -FilePath "workflow.bat" -Encoding ASCII

Write-Host "✓ Created workflow.bat shortcut" -ForegroundColor Green
Write-Host "`n⚠️  REMEMBER: Never copy workflow.py (home version) here!" -ForegroundColor Red