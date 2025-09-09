@echo off
REM Visual Regression Testing Tool - Local Deployment Script (Windows)
REM Usage: deploy-local.bat
REM This script sets up a local Python environment without Docker

echo 🚀 Setting up Visual Regression Testing Tool - Local Environment

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8+ first.
    echo [INFO] Visit: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python version: %PYTHON_VERSION%

REM Check if Python version is compatible (3.8+)
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.8+ is required. Current version: %PYTHON_VERSION%
    echo [INFO] Please upgrade Python or use a different version.
    pause
    exit /b 1
)
echo [INFO] Python %PYTHON_VERSION% detected - using venv for isolation

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed. Please install pip first.
    pause
    exit /b 1
)

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist "venv" (
    echo [WARNING] Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo [INFO] Virtual environment created successfully!

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

REM Install Playwright browsers
echo [INFO] Installing Playwright browsers...
playwright install
if errorlevel 1 (
    echo [ERROR] Failed to install Playwright browsers.
    pause
    exit /b 1
)

REM Install Playwright system dependencies
echo [INFO] Installing Playwright system dependencies...
playwright install-deps
if errorlevel 1 (
    echo [WARNING] Failed to install system dependencies. You may need to install them manually.
    echo [INFO] Visit: https://playwright.dev/python/docs/installation
)

REM Run tests
echo [INFO] Running functionality tests...
python test_functionality.py

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "test_results" mkdir test_results
if not exist "logs" mkdir logs

REM Set up environment variables
echo [INFO] Setting up environment...
if not exist ".env" (
    if exist "env.example" (
        copy env.example .env >nul
        echo [INFO] Created .env file from template
    ) else (
        echo STREAMLIT_SERVER_PORT=8501 > .env
        echo STREAMLIT_SERVER_ADDRESS=0.0.0.0 >> .env
        echo STREAMLIT_SERVER_HEADLESS=true >> .env
        echo [INFO] Created basic .env file
    )
)

REM Start the application
echo [INFO] Starting Visual Regression Testing Tool...
echo [INFO] The application will be available at: http://localhost:8501
echo [INFO] Press Ctrl+C to stop the application
echo.

REM Start Streamlit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
