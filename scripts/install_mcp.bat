@echo off
setlocal enabledelayedexpansion
REM =============================================
REM GitDoc — Install MCP Server Dependencies
REM =============================================

cd /d "%~dp0..\backend"

echo ======================================
echo  GitDoc MCP Server — Install
echo ======================================
echo.

REM --- Find Python ---
set PYTHON_EXE=
for %%p in (python python3 py) do (
    where %%p >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set PYTHON_EXE=%%p
        goto :found
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

echo [ERROR] Python not found.
echo Please install Python 3.10+ from: https://www.python.org/downloads/
pause
exit /b 1

:found
echo Python: %PYTHON_EXE%

REM --- Install core dependencies ---
echo.
echo Installing GitDoc backend dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ======================================
echo  MCP Server installed successfully!
echo ======================================
echo.
echo Next steps — configure your AI assistant:
echo.
echo   Claude Code:
echo     claude mcp add gitdoc -- %PYTHON_EXE% %CD%\mcp_server.py
echo.
echo   Claude Desktop:
echo     Edit claude_desktop_config.json and add:
echo     { "mcpServers": { "gitdoc": { "command": "%PYTHON_EXE%", "args": ["%CD:\=\\%\\mcp_server.py"] } } }
echo.
echo   Cursor / Others:
echo     Add MCP Server with command: %PYTHON_EXE% %CD%\mcp_server.py
echo.
echo   HTTP mode (remote access):
echo     %PYTHON_EXE% %CD%\mcp_server.py --transport http
echo     → Server starts at http://127.0.0.1:18522/mcp
echo.
echo For detailed docs, see: docs\mcp.md
echo ======================================
pause
