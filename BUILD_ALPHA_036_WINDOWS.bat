@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
if not "%~1"=="" set "UE_ROOT=%~1"
set "UBT=%UE_ROOT%\Engine\Build\BatchFiles\Build.bat"
if not exist "%UBT%" (
 echo ERROR: Build.bat not found at "%UBT%"
 echo Usage: BUILD_ALPHA_036_WINDOWS.bat "D:\Epic Games\UE_5.8"
 exit /b 2
)
if not exist "NYVERRA.uproject" (echo ERROR: Missing NYVERRA.uproject & exit /b 3)
echo Building NYVERRAEditor Win64 Development...
call "%UBT%" NYVERRAEditor Win64 Development -Project="%CD%\NYVERRA.uproject" -WaitMutex -NoHotReloadFromIDE > "BUILD_ALPHA_036.log" 2>&1
set "RC=%ERRORLEVEL%"
type "BUILD_ALPHA_036.log"
if not "%RC%"=="0" (echo BUILD FAILED, inspect BUILD_ALPHA_036.log) else (echo BUILD SUCCESS; launch NYVERRA.uproject)
exit /b %RC%
