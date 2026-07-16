@echo off
REM =============================================
REM GitDoc — Build Release Package
REM =============================================
REM Creates a distributable ZIP containing the
REM standalone backend EXE + frontend + scripts.
REM Users don't need Python or Git installed.
REM
REM Prerequisites:
REM   pip install pyinstaller
REM =============================================

setlocal enabledelayedexpansion
cd /d "%~dp0.."

set "RELEASE_DIR=dist\release\GitDoc"
set "ZIP_NAME=GitDoc-v1.0.0.zip"

echo ======================================
echo  GitDoc - Build Release Package
echo ======================================
echo.

REM --- Step 1: Build backend EXE with PyInstaller ---
echo [1/5] Building backend EXE with PyInstaller...

cd backend
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"

pyinstaller ^
    --onefile ^
    --name gitdoc-backend ^
    --hidden-import=docx ^
    --hidden-import=diff_match_patch ^
    --hidden-import=watchdog ^
    --hidden-import=git ^
    --hidden-import=pydantic ^
    --hidden-import=lxml ^
    --hidden-import=docx.opc.parts.coreprops ^
    --hidden-import=docx.opc.parts.extendedprops ^
    --hidden-import=mcp.server.fastmcp ^
    --hidden-import=jieba ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

cd ..

REM --- Step 2: Create release directory ---
echo [2/5] Creating release directory...
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"

REM --- Step 3: Copy files ---
echo [3/5] Copying files...

copy /Y "backend\dist\gitdoc-backend.exe" "%RELEASE_DIR%\" >nul

robocopy "frontend" "%RELEASE_DIR%\frontend" /E /NFL /NDL /NJH /NJS >nul

mkdir "%RELEASE_DIR%\scripts" 2>nul
copy /Y "scripts\gen_cert.bat" "%RELEASE_DIR%\scripts\" >nul
copy /Y "scripts\install_addin.bat" "%RELEASE_DIR%\scripts\" >nul
copy /Y "scripts\install_mcp.bat" "%RELEASE_DIR%\scripts\" >nul

copy /Y "README.md" "%RELEASE_DIR%\" >nul
copy /Y "LICENSE" "%RELEASE_DIR%\" >nul

REM --- Step 4: Create launcher ---
echo [4/5] Creating launcher...
(
    echo @echo off
    echo REM =============================================
    echo REM GitDoc — Launch Backend
    echo REM =============================================
    echo REM Double-click to start. Keep this window open.
    echo REM Then open https://localhost:18521/ in browser.
    echo REM =============================================
    echo.
    echo cd /d "%%~dp0"
    echo.
    echo echo ======================================
    echo echo  GitDoc v1.0.0
    echo echo ======================================
    echo echo.
    echo echo Starting backend...
    echo echo.
    echo echo If no browser opens automatically, visit:
    echo echo   https://localhost:18521/
    echo echo ======================================
    echo echo.
    echo.
    echo start "" https://localhost:18521/
    echo.
    echo gitdoc-backend.exe
    echo.
    echo pause
) > "%RELEASE_DIR%\启动GitDoc.bat"

REM --- Step 5: Create ZIP ---
echo [5/5] Creating ZIP archive...
if exist "dist\%ZIP_NAME%" del /q "dist\%ZIP_NAME%"

powershell -Command ^
    "Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
    "[System.IO.Compression.ZipFile]::CreateFromDirectory('dist\release\GitDoc', 'dist\%ZIP_NAME%')"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ZIP creation failed.
    pause
    exit /b 1
)

echo.
echo ======================================
echo  Build Complete!
echo  Package: dist\%ZIP_NAME%
echo ======================================
echo.
echo To update the GitHub release:
echo   1. Go to https://github.com/xijunyuan/GitDoc/releases/tag/v1.0.0
echo   2. Click "Edit tag"
echo   3. Upload dist\%ZIP_NAME%
echo ======================================
echo.
pause
