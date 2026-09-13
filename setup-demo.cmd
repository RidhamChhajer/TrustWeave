@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if errorlevel 1 goto python
py -3 -m venv ".venv"
if errorlevel 1 goto failed
goto install
:python
python -m venv ".venv"
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto failed
echo Setup complete. See docs\two-device-operation.md for trusted provisioning and device transfer.
pause
exit /b 0
:failed
echo Setup failed. Install Python 3.10 or newer with TLS 1.3 support, check internet access, and retry.
pause
exit /b 1
