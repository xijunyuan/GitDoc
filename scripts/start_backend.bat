@echo off
REM =============================================
REM GitDoc — Start Python Backend
REM =============================================
REM Python: D:\Anaconda3\envs\gitdoc\python.exe (conda gitdoc env, Python 3.11)

cd /d "%~dp0..\backend"

set PYTHON_EXE=D:\Anaconda3\envs\gitdoc\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] GitDoc conda environment not found.
    echo Please run: conda create -n gitdoc python=3.11 -y
    echo Then: D:\Anaconda3\envs\gitdoc\python.exe -m pip install fastapi uvicorn python-docx diff-match-patch GitPython watchdog pydantic
    pause
    exit /b 1
)

echo ======================================
echo  GitDoc Backend v0.1.0
echo  Python: %PYTHON_EXE%
echo  Starting on http://127.0.0.1:18521
echo ======================================
echo.

%PYTHON_EXE% main.py

pause
