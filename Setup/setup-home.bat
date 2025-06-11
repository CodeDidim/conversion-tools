@echo off
title Home Workflow Setup
color 0A

echo ====================================
echo    HOME Workflow Environment Setup
echo ====================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ERROR: Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found
echo.

:: Install dependencies
echo Installing Python dependencies...
python -m pip install requests pyyaml flask
if errorlevel 1 (
    echo WARNING: Some packages may have failed to install
)

:: Check GitHub token
if "%GITHUB_TOKEN%"=="" (
    echo.
    echo WARNING: GITHUB_TOKEN not set!
    echo.
    echo To set temporarily in this session:
    echo   set GITHUB_TOKEN=ghp_your_token_here
    echo.
    echo To set permanently:
    echo   setx GITHUB_TOKEN "ghp_your_token_here"
    echo.
)

:: Create directories
echo Creating directory structure...
if not exist "conversion-tools" mkdir "conversion-tools"
if not exist "conversion-tools\scripts" mkdir "conversion-tools\scripts"
if not exist "conversion-tools\scripts\config_profiles" mkdir "conversion-tools\scripts\config_profiles"

:: Check for required files
echo.
echo Checking for required scripts...
if not exist "conversion-tools\workflow.py" (
    echo WARNING: workflow.py not found
    echo Please copy workflow.py to conversion-tools\
)
if not exist "conversion-tools\visibility-server.py" (
    echo WARNING: visibility-server.py not found
    echo Please copy visibility-server.py to conversion-tools\
)

:: Initialize
echo.
echo Initializing workflow...
python conversion-tools\workflow.py init

:: Create helper batch files
echo.
echo Creating helper scripts...

:: Create workflow.bat
echo @echo off > workflow.bat
echo python conversion-tools\workflow.py %%* >> workflow.bat

:: Create start-server.bat
echo @echo off > start-server.bat
echo title Visibility Server >> start-server.bat
echo echo Starting visibility server... >> start-server.bat
echo python conversion-tools\visibility-server.py >> start-server.bat
echo pause >> start-server.bat

echo.
echo ====================================
echo    Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Set GITHUB_TOKEN environment variable
echo 2. Update .workflow-config.yaml
echo 3. Run start-server.bat to start visibility server
echo 4. Configure router port forwarding for port 8888
echo.
echo Shortcuts created:
echo - workflow.bat (run workflow commands)
echo - start-server.bat (start visibility server)
echo.
pause