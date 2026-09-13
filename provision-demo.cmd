@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
set "chatProvisionTarget=%~dp0demo-identities"
if not "%~1"=="" set "chatProvisionTarget=%~1"
".venv\Scripts\python.exe" -m chat.bundles provision "%chatProvisionTarget%"
set "chatExit=%errorlevel%"
pause
exit /b %chatExit%
:missing
echo Run setup-demo.cmd first.
pause
exit /b 1
