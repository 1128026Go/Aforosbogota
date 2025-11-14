@echo off
setlocal
cd /d "%~dp0"
start "" "%~dp0start_backend.bat"
start "" "%~dp0start_frontend.bat"
endlocal
