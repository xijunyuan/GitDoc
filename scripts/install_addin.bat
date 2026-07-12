@echo off
setlocal enabledelayedexpansion
REM =============================================
REM GitDoc — Install Office Add-in
REM =============================================
REM Copies the add-in manifest to the Office
REM shared folder so Word can discover it.
REM
REM Also checks:
REM   - SSL certificate is trusted
REM   - Backend is reachable
REM =============================================

set "SCRIPT_DIR=%~dp0"
set "MANIFEST_SRC=%SCRIPT_DIR%..\frontend\word-addin\manifest.xml"
set "CERT_FILE=%SCRIPT_DIR%certs\localhost.crt"
set "BACKEND_URL=https://localhost:18521/api/status"

echo ======================================
echo  GitDoc - Install Word Add-in
echo ======================================
echo.

REM ====================================================================
REM Step 0: Check manifest exists
REM ====================================================================
if not exist "%MANIFEST_SRC%" (
    echo [ERROR] Manifest file not found:
    echo         %MANIFEST_SRC%
    echo.
    echo Please make sure you're running this script from the project's
    echo scripts\ directory and all project files are intact.
    pause
    exit /b 1
)

REM ====================================================================
REM Step 1: Check SSL certificate exists and is trusted
REM ====================================================================
echo [1/4] Checking SSL certificate...

if not exist "%CERT_FILE%" (
    echo [WARN] SSL certificate not found. Generating now...
    call "%SCRIPT_DIR%gen_cert.bat"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Certificate generation failed. Cannot proceed.
        pause
        exit /b 1
    )
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$crt = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2('%CERT_FILE%');" ^
    "$valid = $crt.Verify();" ^
    "if ($valid) { Write-Host '  [OK] Certificate is trusted.' } else { Write-Host '  [WARN] Certificate is NOT trusted.'; exit 1 }"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   The SSL certificate is not trusted by your system.
    echo   Without it, Word cannot connect to the GitDoc backend.
    echo.
    echo   Fix: Run  scripts\gen_cert.bat  as Administrator.
    echo        This will generate and trust the certificate automatically.
    echo.
    echo   Or manually trust the cert:
    echo        1. Double-click: scripts\certs\localhost.crt
    echo        2. "Install Certificate..." -- "Local Machine"
    echo        3. "Place all certificates in the following store"
    echo        4. Browse -- "Trusted Root Certification Authorities"
    echo.
    pause
    exit /b 1
)

REM ====================================================================
REM Step 2: Check backend is running
REM ====================================================================
echo [2/4] Checking backend connectivity...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { " ^
    "  $r = Invoke-WebRequest -Uri '%BACKEND_URL%' -UseBasicParsing -TimeoutSec 3 -SkipCertificateCheck;" ^
    "  if ($r.StatusCode -eq 200) { Write-Host '  [OK] Backend is running.'; exit 0 } " ^
    "} catch { " ^
    "  Write-Host '  [WARN] Backend is not reachable.'; exit 1 " ^
    "}"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   The GitDoc backend is not currently running.
    echo   The add-in can be installed, but will not work until the backend starts.
    echo.
    echo   Start the backend first:  scripts\start_backend.bat
    echo.
    choice /c YN /m "Continue with installation anyway"
    if !ERRORLEVEL! EQU 2 exit /b 1
)

REM ====================================================================
REM Step 3: Determine correct WEF folder
REM ====================================================================
echo [3/4] Detecting Office shared add-in folder...

set "WEF_DIR=%LOCALAPPDATA%\Microsoft\Office\16.0\Wef"

REM Office may also install under Program Files variants
if not exist "%WEF_DIR%" (
    for %%v in (16.0 15.0) do (
        if exist "%LOCALAPPDATA%\Microsoft\Office\%%v\Wef" (
            set "WEF_DIR=%LOCALAPPDATA%\Microsoft\Office\%%v\Wef"
            goto :wef_found
        )
    )
    REM Folder doesn't exist yet -- create it
    echo   WEF folder not found, creating...
)

:wef_found
if not exist "%WEF_DIR%" mkdir "%WEF_DIR%" >nul 2>&1
if not exist "%WEF_DIR%" (
    echo [ERROR] Cannot create or find the Office WEF folder.
    echo.
    echo   Make sure Microsoft Word 2016 or later is installed.
    echo   If you've never run Word before, open it once first.
    pause
    exit /b 1
)
echo   Target: %WEF_DIR%

REM ====================================================================
REM Step 4: Copy manifest
REM ====================================================================
echo [4/4] Installing add-in manifest...

copy /Y "%MANIFEST_SRC%" "%WEF_DIR%\GitDoc-Manifest.xml" >nul

if %ERRORLEVEL% EQU 0 (
    echo   [OK] Manifest installed.
) else (
    echo   [ERROR] Failed to copy manifest.
    echo           Try running this script as Administrator.
    pause
    exit /b 1
)

REM ====================================================================
REM Done
REM ====================================================================
echo.
echo ======================================
echo  Installation Complete!
echo ======================================
echo.
echo Next steps:
echo   1. Make sure the backend is running ^(scripts\start_backend.bat^)
echo   2. Open or restart Microsoft Word
echo   3. Click:  Insert ^> My Add-ins ^> Shared Folder
echo   4. Select "GitDoc - 文档版本管理" and click Add
echo.
echo The GitDoc panel will appear on the right side of Word.
echo ======================================

pause
