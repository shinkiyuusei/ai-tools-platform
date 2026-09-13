@echo off
setlocal EnableExtensions

rem Always run relative to this script, even when launched by double-click.
cd /d "%~dp0"
title AI Tools Platform Launcher

echo [1/5] Checking required tools...
where docker >nul 2>&1 || goto :missing_docker
docker compose version >nul 2>&1 || goto :missing_compose
where npm >nul 2>&1 || goto :missing_npm

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>&1 || goto :missing_python
    set "PYTHON_CMD=python"
)

if not exist ".env" (
    echo [2/5] Creating .env from .env.example...
    copy /y ".env.example" ".env" >nul || goto :failed
    echo Please review .env and configure the required API keys.
) else (
    echo [2/5] Using existing .env.
)

echo [3/5] Starting Docker services...
docker compose up -d
if errorlevel 1 goto :docker_failed

if not exist "backend\.venv\Scripts\python.exe" (
    echo [4/5] Creating backend virtual environment...
    %PYTHON_CMD% -m venv "backend\.venv" || goto :failed
)

echo [4/5] Installing/updating backend dependencies...
"backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :failed

if not exist "frontend\node_modules" (
    echo [5/5] Installing frontend dependencies...
    pushd "frontend"
    call npm ci
    if errorlevel 1 (
        popd
        goto :failed
    )
    popd
) else (
    echo [5/5] Frontend dependencies are already installed.
)

echo.
echo Starting backend at http://localhost:5000 ...
start "AI Tools Platform - Backend" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe run.py"

echo Starting frontend at http://localhost:5173 ...
start "AI Tools Platform - Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo All services have been launched.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:5000
timeout /t 3 >nul
exit /b 0

:missing_docker
echo ERROR: Docker was not found. Install/start Docker Desktop and try again.
goto :pause_error

:missing_compose
echo ERROR: Docker Compose is unavailable. Check your Docker installation.
goto :pause_error

:missing_npm
echo ERROR: npm was not found. Install Node.js and try again.
goto :pause_error

:missing_python
echo ERROR: Python 3 was not found. Install Python 3 and try again.
goto :pause_error

:docker_failed
echo ERROR: Docker services failed to start. Make sure Docker Desktop is running.
goto :pause_error

:failed
echo ERROR: Setup failed. Review the output above for details.

:pause_error
echo.
pause
exit /b 1
