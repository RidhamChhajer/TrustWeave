@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
set "chatBundle=%~dp0demo-identities\alice-bundle"
if not "%~1"=="" set "chatBundle=%~1"
".venv\Scripts\python.exe" -m chat.app alice --bundle "%chatBundle%"
set "chatExit=%errorlevel%"
pause
exit /b %chatExit%
:missing
echo Run setup-demo.cmd first.
pause
exit /b 1
