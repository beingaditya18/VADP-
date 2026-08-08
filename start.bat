@echo off
TITLE VADP Localhost Launcher
COLOR 0A
echo ============================================================
echo           VADP Zero-Trust Legal AI Platform
echo              Launching Localhost Development Servers
echo ============================================================
echo.

set ROOT_DIR=%~dp0

echo [1/2] Launching FastAPI Backend Server on http://localhost:8000 ...
start "VADP Backend (Port 8000)" cmd /k "cd /d "%ROOT_DIR%backend" && python -m uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak > NUL

echo [2/2] Launching Next.js 15 Frontend Server on http://localhost:3000 ...
start "VADP Frontend (Port 3000)" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"

echo.
echo ============================================================
echo   SUCCESS! VADP is launching on your system:
echo     - Frontend Portal:  http://localhost:3000
echo     - Backend REST API: http://localhost:8000
echo     - API Interactive Docs: http://localhost:8000/docs
echo ============================================================
echo.
pause
