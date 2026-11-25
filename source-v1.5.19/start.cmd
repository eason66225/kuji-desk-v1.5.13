@echo off
setlocal
cd /d "%~dp0"
set "KUJI_RUNTIME=%~dp0..\..\Runtime\kuji-manager"
if not exist "..\..\AGENTS.md" set "KUJI_RUNTIME=%LOCALAPPDATA%\KujiDesk"
set "KUJI_VENV=%KUJI_RUNTIME%\venv"
if not exist "%KUJI_VENV%\Scripts\python.exe" (
  echo Preparing local runtime...
  python -m venv "%KUJI_VENV%"
  if errorlevel 1 goto failed
)
"%KUJI_VENV%\Scripts\python.exe" -c "import aiohttp, playwright, bs4" >nul 2>&1
if errorlevel 1 (
  "%KUJI_VENV%\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto failed
)
"%KUJI_VENV%\Scripts\python.exe" manager.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo Could not start Kuji Manager. Check the message above.
pause
exit /b 1
