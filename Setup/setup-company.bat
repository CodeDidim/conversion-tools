@echo off
title Company Workflow Setup
color 0E

echo ====================================
echo  COMPANY Workflow Environment Setup
echo ====================================
echo.
echo SECURITY REMINDER:
echo - This is the COMPANY setup
echo - DO NOT copy workflow.py here!
echo - Only use workflow-company.py
echo.

set /p continue="Continue with company setup? (y/n): "
if /i not "%continue%"=="y" exit /b 0

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
python -m pip install requests pyyaml

:: Create directories
echo Creating directory structure...
if not exist "conversion-tools" mkdir "conversion-tools"
if not exist "conversion-tools\scripts" mkdir "conversion-tools\scripts"
if not exist "conversion-tools\scripts\config_profiles" mkdir "conversion-tools\scripts\config_profiles"

:: Security check
if exist "conversion-tools\workflow.py" (
    color 0C
    echo.
    echo SECURITY WARNING: workflow.py found!
    echo This file should NOT be at company!
    set /p delete="Delete it? (y/n): "
    if /i "%delete%"=="y" (
        del "conversion-tools\workflow.py"
        echo [OK] Removed workflow.py
    )
)

:: Check for workflow-company.py
if not exist "conversion-tools\workflow-company.py" (
    echo.
    echo WARNING: workflow-company.py not found
    echo Please copy workflow-company.py to conversion-tools\
    pause
)

:: Initialize
echo.
echo Initializing company workflow...
python conversion-tools\workflow-company.py init

:: Create helper batch file
echo @echo off > workflow.bat
echo python conversion-tools\workflow-company.py %%* >> workflow.bat

echo.
echo ====================================
echo    Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Update .workflow-config-company.yaml
echo 2. Get company_profile.yaml from team
echo 3. Test: workflow check-server
echo 4. Test: workflow emergency
echo.
echo Shortcut created: workflow.bat
echo.
color 0C
echo REMEMBER: Never copy workflow.py here!
color 0E
echo.
pause