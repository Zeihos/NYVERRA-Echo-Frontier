@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA - Current project checks
echo NYVERRA - актуальная проверка Alpha 0.61
if not exist "TEST_ALPHA_061_WINDOWS.bat" (
 echo [ERROR] Не найден TEST_ALPHA_061_WINDOWS.bat.
 echo [ACTION] Выполните git pull origin main.
 exit /b 2
)
call "%~dp0TEST_ALPHA_061_WINDOWS.bat" %*
exit /b %errorlevel%
