@echo off
setlocal
cd /d "%~dp0"
if not exist CrossPlatform\.venv\Scripts\python.exe (
  call CrossPlatform\setup-windows.cmd
  if errorlevel 1 exit /b 1
)
CrossPlatform\.venv\Scripts\python.exe -m pip install -r CrossPlatform\requirements-build.txt
if errorlevel 1 exit /b 1
CrossPlatform\.venv\Scripts\python.exe CrossPlatform\build-desktop.py
exit /b %errorlevel%
