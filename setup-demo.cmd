@echo off
setlocal
cd /d "%~dp0"
if exist ".venv314\Scripts\python.exe" goto install
if exist "%LocalAppData%\Programs\Python\Python314\python.exe" goto localpython
where py >nul 2>nul
if errorlevel 1 goto python
py -3.14 -m venv ".venv314"
if errorlevel 1 goto failed
goto install
:python
python -m chat.check_runtime
if errorlevel 1 goto failed
python -m venv ".venv314"
if errorlevel 1 goto failed
goto install
:localpython
"%LocalAppData%\Programs\Python\Python314\python.exe" -m venv ".venv314"
if errorlevel 1 goto failed
:install
".venv314\Scripts\python.exe" -m chat.check_runtime
if errorlevel 1 goto failed
".venv314\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv314\Scripts\python.exe" -m pip check
if errorlevel 1 goto failed
echo Setup complete. See docs\two-device-operation.md for trusted provisioning and device transfer.
pause
exit /b 0
:failed
echo Setup failed. Install Python 3.14 with OpenSSL 3.0 or newer and TLS 1.3 support, check internet access, and retry.
pause
exit /b 1
