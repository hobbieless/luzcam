@echo off
setlocal
cd /d "%~dp0.."
py -3.12 -m venv CrossPlatform\.venv
if errorlevel 1 (
 echo Instala Python 3.12 de python.org con el lanzador py y vuelve a abrir este archivo.
 pause
 exit /b 1
)
if exist "..\wheels-windows\PySide6-6.8.3-cp39-abi3-win_amd64.whl" (
 CrossPlatform\.venv\Scripts\python.exe -m pip install --no-index --find-links "..\wheels-windows" -r CrossPlatform\requirements.txt
) else (
 CrossPlatform\.venv\Scripts\python.exe -m pip install -r CrossPlatform\requirements.txt
)
if errorlevel 1 (pause & exit /b 1)
CrossPlatform\.venv\Scripts\python.exe Tests\portable-model.py
if errorlevel 1 (pause & exit /b 1)
echo Preparacion completada. Abre iniciar-windows.cmd. El uso posterior no necesita Internet.
pause
