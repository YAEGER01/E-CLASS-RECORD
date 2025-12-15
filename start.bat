@echo off
REM E-Class Record System Startup Script

echo ========================================
echo  E-Class Record System Startup
echo ========================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [ERROR] Failed to activate virtual environment
        echo [INFO] Please create a virtual environment first:
        echo        python -m venv .venv
        pause
        exit /b 1
    )
)

REM Check if dependencies are installed
echo [INFO] Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [WARNING] Flask not found. Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [INFO] Starting Flask application...
echo [INFO] Access the application at: http://127.0.0.1:5000
echo.
echo [INFO] Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error
    pause
)
