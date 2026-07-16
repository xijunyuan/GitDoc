@echo off
setlocal enabledelayedexpansion
REM =============================================
REM GitDoc — Start Python Backend
REM =============================================
REM Auto-detects Python 3.10+ on the system.
REM Falls back to common install locations.
REM =============================================

cd /d "%~dp0..\backend"

echo ======================================
echo  GitDoc Backend v1.0.0
echo ======================================
echo.

REM --- Find Python 3.10+ ---
set PYTHON_EXE=
for %%p in (python python3 py) do (
    where %%p >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        for /f "delims=" %%v in ('%%p -c "import sys; print(sys.version_info[:2])" 2^>nul') do (
            set "VER=%%v"
            if "!VER!" GEQ "(3, 10)" (
                set PYTHON_EXE=%%p
                goto :found
            )
        )
    )
)

REM Fallback: check common install locations
for %%d in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "C:\Python313" "C:\Python312" "C:\Python311" "C:\Python310"
    "D:\Python313"  "D:\Python312"  "D:\Python311"  "D:\Python310"
) do (
    if exist "%%~d\python.exe" (
        set "PYTHON_EXE=%%~d\python.exe"
        goto :found
    )
)

echo [ERROR] Python 3.10+ not found.
echo.
echo Please install Python from: https://www.python.org/downloads/
echo IMPORTANT: Check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found
echo Python:   %PYTHON_EXE%
echo Location: %CD%
echo Port:     http://127.0.0.1:18521
echo Docs:     http://127.0.0.1:18521/docs
echo.
echo The backend serves via HTTPS by default.
echo Keep this window open while using GitDoc.
echo ======================================
echo.

"%PYTHON_EXE%" main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Backend failed to start.
    echo Common causes:
    echo   1. Dependencies not installed -- run: pip install -r requirements.txt
    echo   2. Port 18521 already in use -- close other instances first
    echo   3. Python version too old -- need 3.10+
)

pause
