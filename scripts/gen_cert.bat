@echo off
REM =============================================
REM GitDoc — Generate & Trust SSL Certificate
REM =============================================
REM Generates a self-signed cert for localhost
REM and installs it into the Windows Trusted Root store.
REM Requires: OpenSSL and Administrator privileges.
REM =============================================

cd /d "%~dp0certs"

echo ======================================
echo  GitDoc - SSL Certificate Setup
echo ======================================
echo.

REM Generate self-signed certificate
echo [1/2] Generating self-signed certificate...
openssl req -x509 -newkey rsa:2048 -keyout localhost.key -out localhost.crt -days 3650 -nodes -subj "//CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to generate certificate. Is OpenSSL installed?
    pause
    exit /b 1
)
echo [OK] Certificate generated.

REM Trust in Windows cert store (requires Admin)
echo [2/2] Trusting certificate (requires Administrator)...
certutil -addstore Root localhost.crt
if %ERRORLEVEL% EQU 0 (
    echo [OK] Certificate trusted.
) else (
    echo [WARN] Could not trust certificate automatically.
    echo        Run this script as Administrator, or manually trust:
    echo          1. Double-click scripts\certs\localhost.crt
    echo          2. Install Certificate -^> Local Machine
    echo          3. Place in Trusted Root Certification Authorities
)

echo.
echo Done. The backend can now serve HTTPS on localhost.
pause
