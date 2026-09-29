@echo off
REM Double-click this to run the bot. Closing the window stops it.
cd /d "%~dp0"
title Factory Accident Support Bot

REM Pick the interpreter that actually has the ML stack, rather than assuming
REM a version. This used to hardcode "py -3.11" and the stack later ended up
REM installed under 3.14 instead - the server then started, served the page,
REM and failed on every question at retrieval, which looks like a broken bot
REM rather than a missing wheel.
set "PY="
for %%V in (3.11 3.12 3.13 3.14) do (
    if not defined PY (
        py -%%V -c "import chromadb" >nul 2>&1 && set "PY=py -%%V"
    )
)
if not defined PY (
    python -c "import chromadb" >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo   ERROR: no Python on this machine has chromadb installed.
    echo   Install it with:  py -3.14 -m pip install chromadb sentence-transformers
    echo.
    pause
    exit /b 1
)
echo   Using %PY%

echo ============================================================
echo   Factory Accident Support Bot
echo ============================================================
echo.

if not exist ".env" (
    echo   ERROR: .env not found in this folder.
    echo   Copy .env.example to .env and fill it in first.
    echo.
    pause
    exit /b 1
)

findstr /b /c:"GROQ_API_KEY=gsk_" .env >nul 2>&1
if errorlevel 1 (
    echo   WARNING: no Groq key found in .env.
    echo   The bot will still run, but every answer will be a handoff
    echo   instead of a real answer.
    echo.
)

echo   Starting. First run takes about 15 seconds while the
echo   embedding model loads - the browser opens by itself.
echo.
echo   Chat here:  http://localhost:8000
echo   Status:     http://localhost:8000/health
echo.
echo   Leave this window OPEN. Closing it stops the bot.
echo ============================================================
echo.

REM Open the browser once the server has had time to come up.
start "" cmd /c "timeout /t 18 >nul & start http://localhost:8000"

%PY% -m uvicorn server:app --port 8000

echo.
echo   Server stopped.
pause
