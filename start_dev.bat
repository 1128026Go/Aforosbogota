@echo off
setlocal
start "Aforos Backend" cmd /k "%~dp0start_backend.bat"
start "Aforos Frontend" cmd /k "%~dp0start_frontend.bat"

