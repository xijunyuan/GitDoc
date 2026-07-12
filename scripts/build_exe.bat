@echo off
REM =============================================
REM GitDoc — Build Standalone Python Backend EXE
REM =============================================
REM Uses PyInstaller to create a single executable
REM for the GitDoc backend, so users don't need
REM to install Python to use the plugin.
REM
REM Prerequisites:
REM   pip install pyinstaller
REM =============================================

echo ======================================
echo  GitDoc - Build Backend EXE
echo ======================================
echo.

cd /d "%~dp0..\backend"

echo [1/3] Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

echo [2/3] Running PyInstaller...
pyinstaller ^
    --onefile ^
    --name gitdoc-backend ^
    --add-data "requirements.txt;." ^
    --hidden-import=docx ^
    --hidden-import=diff_match_patch ^
    --hidden-import=watchdog ^
    --hidden-import=git ^
    --hidden-import=pydantic ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo [3/3] Copying output...
copy /Y "dist\gitdoc-backend.exe" "..\scripts\" >nul

echo.
echo ======================================
echo  Build Complete!
echo  Output: scripts\gitdoc-backend.exe
echo ======================================
echo.
pause
