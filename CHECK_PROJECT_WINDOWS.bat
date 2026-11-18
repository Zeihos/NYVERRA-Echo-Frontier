@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA - Current project checks
echo NYVERRA - current Alpha 0.63 source checks and UE build
if not exist "TEST_ALPHA_063_WINDOWS.bat" (
 echo [ERROR] TEST_ALPHA_063_WINDOWS.bat not found.
 echo [ACTION] Run git pull origin main.
 exit /b 2
)
call "%~dp0TEST_ALPHA_063_WINDOWS.bat" %*
exit /b %errorlevel%
