@echo off
echo ========================================
echo    HCP CRM - Starting Application
echo ========================================
echo.

REM Start Backend
echo Starting Backend Server...
start "HCP CRM Backend" cmd /k "cd /d D:\assignmentproaicrm\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start Frontend
echo Starting Frontend Server...
start "HCP CRM Frontend" cmd /k "cd /d D:\assignmentproaicrm\frontend && npm run dev"

echo.
echo ========================================
echo    Application Starting...
echo ========================================
echo    Backend: http://localhost:8000
echo    Frontend: http://localhost:5173
echo    API Docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul
