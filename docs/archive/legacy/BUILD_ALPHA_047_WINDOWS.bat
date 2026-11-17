@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "UE_ROOT=%~1"
if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "BUILDER=%UE_ROOT%\Engine\Build\BatchFiles\Build.bat"
set "EDITOR=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=%CD%\NYVERRA.uproject"
if not exist "%BUILDER%" (
 echo [ERROR] Build.bat not found in "%UE_ROOT%"
 echo Usage: BUILD_ALPHA_047_WINDOWS.bat "D:\Epic Games\UE_5.8"
 exit /b 2
)
if not exist "%PROJECT%" (echo [ERROR] Project file missing & exit /b 3)
if not exist "%EDITOR%" (echo [WARN] UnrealEditor.exe not found; C++ build will still be attempted.)
echo [NYVERRA 0.47] Starting UnrealBuildTool build...
call "%BUILDER%" NYVERRAEditor Win64 Development -Project="%PROJECT%" -WaitMutex -NoHotReloadFromIDE > "%CD%\BUILD_ALPHA_047.log" 2>&1
set "RESULT=%ERRORLEVEL%"
type "%CD%\BUILD_ALPHA_047.log"
if not "%RESULT%"=="0" (
 echo [FAILED] Build failed, errorlevel %RESULT%. See BUILD_ALPHA_047.log
 exit /b %RESULT%
)
echo [SUCCESS] C++ editor target built. This does not verify level setup or multiplayer.
echo Open NYVERRA.uproject and create/save TestWorld before gameplay tests.
exit /b 0
