@echo off
REM =============================================
REM GitDoc — Sideload Word Add-in
REM =============================================
REM Two methods for Word 2024 / Microsoft 365:
REM   Method 1 (recommended): Upload My Add-in
REM   Method 2 (fallback): Manual Trusted Catalog
REM =============================================

cd /d "%~dp0.."

set MANIFEST=%CD%\frontend\word-addin\manifest.xml

if not exist "%MANIFEST%" (
    echo [ERROR] Manifest not found: %MANIFEST%
    pause
    exit /b 1
)

echo ======================================
echo  GitDoc - Sideload Word Add-in
echo ======================================
echo.
echo Manifest location:
echo   %MANIFEST%
echo.
echo ======================================
echo   Method 1: Upload My Add-in (recommended)
echo ======================================
echo.
echo   1. Open Microsoft Word
echo   2. Insert tab ^> Add-ins ^> Upload My Add-in
echo      (or: Home tab ^> Add-ins ^> More Add-ins ^> My Add-ins ^> Upload)
echo   3. Browse to: %MANIFEST%
echo   4. Click Open, then Trust this add-in
echo.
echo   If "Upload My Add-in" is not visible:
echo.
echo ======================================
echo   Method 2: Developer Tab
echo ======================================
echo.
echo   1. File ^> Options ^> Customize Ribbon
echo   2. Check "Developer" on the right panel, click OK
echo   3. Developer tab ^> Add-ins ^> Upload My Add-in
echo      (or: Developer tab ^> Add-ins ^> Shared Folder)
echo   4. Browse to: %MANIFEST%
echo.

start "" "%CD%\frontend\word-addin"

echo Explorer opened to the manifest location.
echo Drag manifest.xml into the upload dialog if needed.
pause
