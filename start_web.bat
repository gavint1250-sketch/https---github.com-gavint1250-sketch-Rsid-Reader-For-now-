@echo off
REM ─────────────────────────────────────────────────────────────────────────
REM start_web.bat  —  Windows startup script
REM
REM Double-click this file (or run it from a terminal) to install
REM dependencies and start the web app at http://localhost:5000
REM ─────────────────────────────────────────────────────────────────────────
cd /d "%~dp0"

echo.
echo  Document Integrity Analyzer
echo  ============================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python was not found.
    echo  Please install Python 3.8 or newer from https://www.python.org
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo  Installing / updating dependencies into libs\ ...
echo  (This may take several minutes the first time - torch is large)
echo.

REM Flask
python -m pip install --target libs\ flask --quiet
if errorlevel 1 (
    echo  WARNING: flask install may have had issues. Continuing...
)

REM All other deps with CPU-only torch (saves ~1.8 GB vs the default CUDA build)
python -m pip install --target libs\ -r requirements_web.txt ^
    --index-url https://download.pytorch.org/whl/cpu --quiet
if errorlevel 1 (
    REM Retry without the quiet flag so the user can see what went wrong
    echo.
    echo  Retrying dependency install (showing output)...
    python -m pip install --target libs\ -r requirements_web.txt ^
        --index-url https://download.pytorch.org/whl/cpu
)

echo.
echo  Starting server...
echo  Opening http://localhost:5000 in your browser.
echo  Press Ctrl+C in this window to stop the server.
echo.

REM Open the browser a moment after the server starts
start "" /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

python web_app.py

echo.
echo  Server stopped.
pause
