# Setup script for home environment on Windows
# Run as: powershell -ExecutionPolicy Bypass -File setup-home.ps1

Write-Host "🏠 Setting up HOME workflow environment..." -ForegroundColor Green

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
python -m pip install requests pyyaml flask

# Check for GitHub token
if (-not $env:GITHUB_TOKEN) {
    Write-Host "⚠️  GITHUB_TOKEN not set!" -ForegroundColor Yellow
    Write-Host "   To set temporarily: `$env:GITHUB_TOKEN='ghp_your_token'" -ForegroundColor Yellow
    Write-Host "   To set permanently: [Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'ghp_your_token', 'User')" -ForegroundColor Yellow
}

# Create directory structure
Write-Host "→ Creating directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "conversion-tools" | Out-Null
New-Item -ItemType Directory -Force -Path "conversion-tools\scripts" | Out-Null
New-Item -ItemType Directory -Force -Path "conversion-tools\scripts\config_profiles" | Out-Null

# Download workflow scripts (replace with actual URLs or copy from local)
Write-Host "→ Setting up workflow scripts..." -ForegroundColor Yellow

# Check if scripts exist
$scriptsToCheck = @(
    "conversion-tools\workflow.py",
    "conversion-tools\visibility-server.py"
)

$missingScripts = @()
foreach ($script in $scriptsToCheck) {
    if (-not (Test-Path $script)) {
        $missingScripts += $script
    }
}

if ($missingScripts.Count -gt 0) {
    Write-Host "⚠️  Missing scripts:" -ForegroundColor Yellow
    $missingScripts | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    Write-Host "`nPlease copy these files to the conversion-tools directory" -ForegroundColor Yellow
    
    # Optionally download from GitHub
    $download = Read-Host "Download from GitHub? (y/n)"
    if ($download -eq 'y') {
        # Replace with your actual GitHub URLs
        $baseUrl = "https://raw.githubusercontent.com/YOUR_REPO/main"
        
        Write-Host "Downloading workflow.py..."
        Invoke-WebRequest -Uri "$baseUrl/workflow.py" -OutFile "conversion-tools\workflow.py"
        
        Write-Host "Downloading visibility-server.py..."
        Invoke-WebRequest -Uri "$baseUrl/visibility-server.py" -OutFile "conversion-tools\visibility-server.py"
    }
}

# Initialize workflow
Write-Host "→ Initializing workflow..." -ForegroundColor Yellow
Set-Location -Path (Get-Location)
python conversion-tools\workflow.py init

Write-Host "`n✅ Home setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Set GITHUB_TOKEN environment variable" -ForegroundColor White
Write-Host "   [Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'ghp_your_token', 'User')" -ForegroundColor Gray
Write-Host "2. Update .workflow-config.yaml with your GitHub details" -ForegroundColor White
Write-Host "3. Start visibility server:" -ForegroundColor White
Write-Host "   python conversion-tools\visibility-server.py" -ForegroundColor Gray
Write-Host "4. Configure port forwarding on your router for port 8888" -ForegroundColor White

# Create convenient shortcuts
Write-Host "`n→ Creating convenient shortcuts..." -ForegroundColor Yellow

# Create start-server.bat
@"
@echo off
echo Starting visibility server...
python conversion-tools\visibility-server.py
pause
"@ | Out-File -FilePath "start-server.bat" -Encoding ASCII

# Create workflow shortcuts
@"
@echo off
python conversion-tools\workflow.py %*
"@ | Out-File -FilePath "workflow.bat" -Encoding ASCII

Write-Host "✓ Created workflow.bat and start-server.bat shortcuts" -ForegroundColor Green