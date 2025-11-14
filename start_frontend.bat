@echo off
setlocal
cd /d "%~dp0apps\web"
npm run dev -- --host 0.0.0.0 --port 5173
endlocal
