@echo off
setlocal

set "GIT_BASH=C:\Program Files\Git\bin\bash.exe"
if exist "%GIT_BASH%" (
  "%GIT_BASH%" %*
  exit /b %ERRORLEVEL%
)

set "WSL_BASH=%SystemRoot%\System32\bash.exe"
if exist "%WSL_BASH%" (
  "%WSL_BASH%" %*
  exit /b %ERRORLEVEL%
)

echo bash runtime not found
exit /b 1
