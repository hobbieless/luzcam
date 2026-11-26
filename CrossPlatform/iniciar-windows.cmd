@echo off
setlocal
cd /d "%~dp0.."
if not exist CrossPlatform\.venv\Scripts\python.exe (
 echo Ejecuta setup-windows.cmd una vez antes de iniciar.
 pause
 exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
exit /b 0
