@echo off
setlocal
cd /d "%~dp0"
set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
if not "%~1"=="" set "UE_ROOT=%~1"
set "UBT=%UE_ROOT%\Engine\Build\BatchFiles\Build.bat"
if not exist "%UBT%" (
 echo ERROR: Unreal Build.bat not found: "%UBT%"
 echo Usage: BUILD_ALPHA_033_WINDOWS.bat "D:\Epic Games\UE_5.8"
 exit /b 2
)
if not exist "NYVERRA.uproject" (echo ERROR: Missing NYVERRA.uproject & exit /b 3)
echo Compiling NYVERRAEditor for Win64 Development...
call "%UBT%" NYVERRAEditor Win64 Development -Project="%CD%\NYVERRA.uproject" -WaitMutex -NoHotReloadFromIDE > "BUILD_ALPHA_033.log" 2>&1
set "RESULT=%ERRORLEVEL%"
type "BUILD_ALPHA_033.log"
if not "%RESULT%"=="0" echo FAILED: send BUILD_ALPHA_033.log for a targeted fix.
if "%RESULT%"=="0" echo BUILD SUCCEEDED: next open project in Unreal Editor and create/save TestWorld.
exit /b %RESULT%
