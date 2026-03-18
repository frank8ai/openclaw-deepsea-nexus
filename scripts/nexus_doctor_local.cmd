@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS1=%SCRIPT_DIR%nexus_doctor_local.ps1"

if not exist "%PS1%" (
  echo PowerShell doctor script not found: "%PS1%"
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%PS1%" %*
exit /b %ERRORLEVEL%
