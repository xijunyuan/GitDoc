@echo off
REM =============================================
REM GitDoc — Generate & Trust SSL Certificate
REM =============================================
REM Uses PowerShell (built into Windows) to:
REM   1. Generate a self-signed cert for localhost
REM   2. Install it into the Trusted Root store
REM No OpenSSL required.
REM =============================================

cd /d "%~dp0certs"

echo ======================================
echo  GitDoc - SSL Certificate Setup
echo ======================================
echo.

REM ====================================================================
REM Step 1: Generate self-signed certificate via PowerShell
REM ====================================================================
echo [1/2] Generating self-signed certificate...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$cert = New-SelfSignedCertificate -DnsName 'localhost','127.0.0.1' -CertStoreLocation 'Cert:\CurrentUser\My' -KeyExportPolicy Exportable -NotAfter (Get-Date).AddYears(10);" ^
    "$cert | Export-Certificate -FilePath 'localhost.crt' -Type CERT;" ^
    "Write-Host '  Cert thumbprint:' $cert.Thumbprint"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to generate certificate.
    pause
    exit /b 1
)
echo [OK] Certificate files created.

REM ====================================================================
REM Step 2: Trust certificate in Windows cert store
REM ====================================================================
echo.
echo [2/2] Trusting certificate ^(requires Administrator^)...
echo        A UAC prompt may appear -- please click "Yes".

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$certFile = Join-Path $PSScriptRoot 'localhost.crt';" ^
    "$store = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root','CurrentUser');" ^
    "$store.Open('ReadWrite');" ^
    "$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certFile);" ^
    "$store.Add($cert);" ^
    "$store.Close();" ^
    "Write-Host '  Certificate trusted for CurrentUser\Root'"

if %ERRORLEVEL% EQU 0 (
    echo [OK] Certificate is now trusted.
) else (
    echo [WARN] Could not trust certificate automatically.
    echo.
    echo   Try running this script as Administrator, or do it manually:
    echo     1. Double-click scripts\certs\localhost.crt
    echo     2. Click "Install Certificate..."
    echo     3. Select "Current User" or "Local Machine"
    echo     4. Choose "Place all certificates in the following store"
    echo     5. Browse -^> "Trusted Root Certification Authorities"
    echo     6. Finish
)

echo.
echo ======================================
echo Done. The backend can now serve HTTPS.
echo Run start_backend.bat to launch.
echo ======================================
pause
