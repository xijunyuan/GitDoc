@echo off
REM =============================================
REM GitDoc — Install Office Add-in (Developer)
REM =============================================
REM This script registers the GitDoc Word add-in
REM by copying the manifest to the appropriate
REM Office add-ins folder for development/testing.
REM
REM Prerequisites:
REM   - Microsoft Word 2016 or later
REM   - Developer mode enabled in Word
REM =============================================

echo ======================================
echo  GitDoc - Install Word Add-in
echo ======================================
echo.

REM Detect Office version and set manifest path
set MANIFEST_PATH=%~dp0..\frontend\word-addin\manifest.xml

if not exist "%MANIFEST_PATH%" (
    echo [ERROR] Manifest file not found: %MANIFEST_PATH%
    pause
    exit /b 1
)

REM Create the wef folder if it doesn't exist
set WEF_DIR=%LOCALAPPDATA%\Microsoft\Office\16.0\Wef
if not exist "%WEF_DIR%" mkdir "%WEF_DIR%"

REM Copy manifest
copy /Y "%MANIFEST_PATH%" "%WEF_DIR%\GitDoc-Manifest.xml"

if %ERRORLEVEL% EQU 0 (
    echo [OK] Add-in manifest installed successfully.
    echo.
    echo Next steps:
    echo   1. Start the Python backend: python backend\main.py
    echo   2. Open Word
    echo   3. Go to Insert ^> My Add-ins ^> Shared Folder
    echo   4. Select "GitDoc - 文档版本管理"
    echo.
    echo To uninstall, delete: %WEF_DIR%\GitDoc-Manifest.xml
) else (
    echo [ERROR] Failed to copy manifest.
    echo Try running this script as Administrator.
)

pause
