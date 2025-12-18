@echo off
REM Installation script for CodeAtlas (Windows Batch)
setlocal enabledelayedexpansion

REM Check for uninstall flag
if "%1"=="--uninstall" goto :uninstall
if "%1"=="-u" goto :uninstall
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help

echo.
echo ========================================
echo   CodeAtlas Installation
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected
echo.

REM Get project path
set "PROJECT_PATH=%~dp0"
set "PROJECT_PATH=%PROJECT_PATH:~0,-1%"
echo Project path: %PROJECT_PATH%
echo.

REM Ask for venv location
set /p VENV_PATH="Virtual environment location [venv]: "
if "!VENV_PATH!"=="" set "VENV_PATH=venv"

REM Ask for dev dependencies
set /p INSTALL_DEV="Install development dependencies? [y/N]: "
if /i "!INSTALL_DEV!"=="y" (
    set "INSTALL_DEV_FLAG=[dev]"
) else (
    set "INSTALL_DEV_FLAG="
)

echo.

REM Check if venv exists
if exist "%VENV_PATH%" (
    set /p RECREATE="Virtual environment already exists. Recreate? [y/N]: "
    if /i "!RECREATE!"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q "%VENV_PATH%"
    ) else (
        goto :install
    )
)

REM Create virtual environment
echo Creating virtual environment at %VENV_PATH%...
python -m venv "%VENV_PATH%"
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    exit /b 1
)
echo [OK] Virtual environment created successfully
echo.

:install
REM Upgrade pip
echo Upgrading pip...
"%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools --quiet
echo.

REM Install CodeAtlas
echo Installing CodeAtlas...
if "!INSTALL_DEV_FLAG!"=="" (
    "%VENV_PATH%\Scripts\pip.exe" install -e . --quiet
) else (
    "%VENV_PATH%\Scripts\pip.exe" install -e ".[dev]" --quiet
)

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [OK] Dependencies installed successfully
echo.

REM Ask for optional tools
set /p INSTALL_TOOLS="Install optional security tools? (bandit, safety, pip-audit) [y/N]: "
if /i "!INSTALL_TOOLS!"=="y" (
    echo Installing optional tools...
    "%VENV_PATH%\Scripts\pip.exe" install bandit safety pip-audit pip-licenses --quiet
    echo [OK] Optional tools installed
    echo.
)

REM Verify installation
echo Verifying installation...
"%VENV_PATH%\Scripts\codeatlas.exe" version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Verification failed, but installation may still be successful
) else (
    echo [OK] Installation verified successfully!
    "%VENV_PATH%\Scripts\codeatlas.exe" version
)
echo.

REM Show usage
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Getting Started:
echo.
echo 1. Activate the virtual environment:
echo    %VENV_PATH%\Scripts\activate
echo.
echo 2. Run CodeAtlas:
echo    codeatlas --help
echo    codeatlas scan .
echo.
echo Or use directly:
echo    %VENV_PATH%\Scripts\codeatlas.exe scan .
echo.

endlocal
exit /b 0

:help
echo CodeAtlas Installation Script
echo.
echo Usage:
echo   install.bat              Install CodeAtlas
echo   install.bat --uninstall  Uninstall CodeAtlas
echo   install.bat --uninstall --remove-config  Uninstall and remove config
echo.
exit /b 0

:uninstall
setlocal enabledelayedexpansion
echo.
echo ========================================
echo   CodeAtlas Uninstall
echo ========================================
echo.

REM Get project path
set "PROJECT_PATH=%~dp0"
set "PROJECT_PATH=%PROJECT_PATH:~0,-1%"

REM Find virtual environments
set "FOUND_VENV="
set "VENV_COUNT=0"

if exist "%PROJECT_PATH%\venv" (
    if exist "%PROJECT_PATH%\venv\Scripts\python.exe" (
        set "FOUND_VENV=%PROJECT_PATH%\venv"
        set /a VENV_COUNT+=1
    )
)
if exist "%PROJECT_PATH%\.venv" (
    if exist "%PROJECT_PATH%\.venv\Scripts\python.exe" (
        if "!VENV_COUNT!"=="0" (
            set "FOUND_VENV=%PROJECT_PATH%\.venv"
        ) else (
            set "FOUND_VENV=!FOUND_VENV! %PROJECT_PATH%\.venv"
        )
        set /a VENV_COUNT+=1
    )
)
if exist "%PROJECT_PATH%\env" (
    if exist "%PROJECT_PATH%\env\Scripts\python.exe" (
        if "!VENV_COUNT!"=="0" (
            set "FOUND_VENV=%PROJECT_PATH%\env"
        ) else (
            set "FOUND_VENV=!FOUND_VENV! %PROJECT_PATH%\env"
        )
        set /a VENV_COUNT+=1
    )
)

if "!VENV_COUNT!"=="0" (
    echo [WARNING] No virtual environment found to uninstall
    endlocal
    exit /b 0
)

REM Select venv if multiple
set "VENV_PATH="
if "!VENV_COUNT!"=="1" (
    for %%v in (!FOUND_VENV!) do set "VENV_PATH=%%v"
    echo Found virtual environment: !VENV_PATH!
) else (
    echo Multiple virtual environments found:
    set "IDX=0"
    for %%v in (!FOUND_VENV!) do (
        set /a IDX+=1
        echo   !IDX!. %%v
    )
    set /p CHOICE="Select virtual environment to remove (number): "
    set "IDX=0"
    for %%v in (!FOUND_VENV!) do (
        set /a IDX+=1
        if !IDX!==!CHOICE! set "VENV_PATH=%%v"
    )
    if "!VENV_PATH!"=="" (
        echo [ERROR] Invalid selection
        endlocal
        exit /b 1
    )
)

REM Confirm removal
set /p CONFIRM="Remove virtual environment at !VENV_PATH!? [y/N]: "
if /i not "!CONFIRM!"=="y" (
    echo Uninstall cancelled
    endlocal
    exit /b 0
)

REM Remove virtual environment
echo Removing virtual environment...
rmdir /s /q "!VENV_PATH!"
if errorlevel 1 (
    echo [ERROR] Failed to remove virtual environment
    endlocal
    exit /b 1
)
echo [OK] Virtual environment removed successfully

REM Remove config if requested
if "%2"=="--remove-config" (
    if exist "%PROJECT_PATH%\.codeatlas" (
        rmdir /s /q "%PROJECT_PATH%\.codeatlas"
        echo [OK] Removed config: .codeatlas
    )
    if exist "%USERPROFILE%\.config\CodeAtlas" (
        rmdir /s /q "%USERPROFILE%\.config\CodeAtlas"
        echo [OK] Removed config: %USERPROFILE%\.config\CodeAtlas
    )
)

echo.
echo ========================================
echo   Uninstall Complete!
echo ========================================
echo.
echo CodeAtlas has been uninstalled successfully!
echo All virtual environment files have been removed.
echo.
endlocal
exit /b 0
