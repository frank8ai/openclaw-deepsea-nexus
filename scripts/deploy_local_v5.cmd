@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

pushd "%ROOT_DIR%" >nul
call ".\bash.cmd" "scripts/deploy_local_v5.sh" %*
set "RC=%ERRORLEVEL%"
popd >nul

exit /b %RC%
