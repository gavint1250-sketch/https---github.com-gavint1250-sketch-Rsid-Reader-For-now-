@echo off
REM ─────────────────────────────────────────────────────────────────────────
REM start_web.bat  —  Windows startup script
REM
REM Double-click this file to install dependencies and start the web app.
REM
REM ACCESS OPTIONS (choose one):
REM   A) Local only     — no extra setup, open http://localhost:5000
REM   B) Same network   — others on your Wi-Fi use http://<your-IP>:5000
REM   C) Any network    — install ngrok (free), then re-run this script;
REM                       a public https://xxxxx.ngrok-free.app URL is shown
REM
REM HOW TO INSTALL NGROK (for option C):
REM   1. Go to https://ngrok.com and create a free account
REM   2. Download the Windows ZIP, extract ngrok.exe somewhere on your PATH
REM      (e.g. C:\Windows\System32, or the same folder as this file)
REM   3. Run:  ngrok config add-authtoken <your-token>
REM   4. Re-run this script — it will detect ngrok automatically
REM ─────────────────────────────────────────────────────────────────────────
cd /d "%~dp0"

echo.
echo  Document Integrity Analyzer
echo  ============================
echo.

REM ── Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python was not found.
    echo  Please install Python 3.8 or newer from https://www.python.org
    echo  During installation, check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM ── Install dependencies ───────────────────────────────────────────────────
echo  Installing / updating dependencies into libs\ ...
echo  (This may take several minutes the first time - torch is ~200 MB)
echo.

python -m pip install --target libs\ flask --quiet
if errorlevel 1 (
    echo  WARNING: flask install reported an issue. Continuing...
)

REM CPU-only torch saves ~1.8 GB vs the default CUDA build
python -m pip install --target libs\ -r requirements_web.txt ^
    --index-url https://download.pytorch.org/whl/cpu --quiet
if errorlevel 1 (
    echo.
    echo  Retrying with output visible...
    python -m pip install --target libs\ -r requirements_web.txt ^
        --index-url https://download.pytorch.org/whl/cpu
)

echo.

REM ── Detect ngrok ──────────────────────────────────────────────────────────
set USE_NGROK=0
where ngrok >nul 2>&1
if not errorlevel 1 set USE_NGROK=1

REM Also check if ngrok.exe is in the same folder as this script
if exist "%~dp0ngrok.exe" set USE_NGROK=1

REM ── Start Flask in background, then start tunnel or open browser ───────────
if "%USE_NGROK%"=="1" (
    echo  ngrok detected — starting public tunnel...
    echo  The public URL will appear in the ngrok window below.
    echo  Share that URL with anyone on any network.
    echo.
    echo  Press Ctrl+C in the ngrok window to stop everything.
    echo.

    REM Start Flask server silently in the background
    start "" /b python web_app.py

    REM Give Flask a moment to start, then launch ngrok in the foreground
    timeout /t 3 /nobreak >nul
    ngrok http 5000
) else (
    echo  Starting server at http://localhost:5000
    echo.
    echo  To allow access from OTHER networks, install ngrok:
    echo    https://ngrok.com  (free account, takes 2 minutes)
    echo  Then re-run this script.
    echo.
    echo  Press Ctrl+C in this window to stop the server.
    echo.

    REM Open browser after a short delay
    start "" /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

    python web_app.py
)

echo.
echo  Server stopped.
pause
