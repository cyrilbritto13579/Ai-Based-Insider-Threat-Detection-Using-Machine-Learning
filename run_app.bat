@echo off
echo ================================================================
echo   Starting Super Admin (FastAPI Backend + React Frontend)
echo ================================================================
echo.

echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Super Admin Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

echo Starting React + Vite Frontend on http://localhost:5173 ...
start "Super Admin Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ================================================================
echo   Both services are launching in separate windows!
echo   - Frontend: http://localhost:5173
echo   - Backend API Docs: http://127.0.0.1:8000/docs
echo ================================================================
pause
