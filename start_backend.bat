@echo off
setlocal
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 3004 --reload
endlocal
