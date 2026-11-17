@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "UE_ROOT=%~1"
if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "BUILDER=%UE_ROOT%\Engine\Build\BatchFiles\Build.bat"
if not exist "%BUILDER%" (
  echo [ERROR] Unreal Build.bat missing: "%BUILDER%"
  echo Usage: BUILD_ALPHA_046_WINDOWS.bat "D:\Epic Games\UE_5.8"
  exit /b 2
)
if not exist "NYVERRA.uproject" (echo [ERROR] NYVERRA.uproject missing & exit /b 3)
set "PROJECT=%CD%\NYVERRA.uproject"
echo Building NYVERRAEditor Win64 Development...
call "%BUILDER%" NYVERRAEditor Win64 Development -Project="%PROJECT%" -WaitMutex -NoHotReloadFromIDE > "%CD%\BUILD_ALPHA_046.log" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%CD%\BUILD_ALPHA_046.log"
if not "%RESULT%"=="0" (
  echo [FAILED] See BUILD_ALPHA_046.log
  exit /b %RESULT%
)
echo [SUCCESS] Unreal C++ build completed. Open NYVERRA.uproject in UE Editor.
exit /b 0
