@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "UE_ROOT=%~1"
if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "BUILDER=%UE_ROOT%\Engine\Build\BatchFiles\Build.bat"
set "EDITOR=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=%CD%\NYVERRA.uproject"
set "LOG=%CD%\BUILD_ALPHA_051.log"
set "ERRS=%CD%\BUILD_ALPHA_051_ERRORS.txt"
if not exist "%PROJECT%" (echo [ERROR] Missing NYVERRA.uproject & exit /b 2)
if not exist "%BUILDER%" (
 echo [ERROR] Unreal Build.bat not found: "%BUILDER%"
 echo Usage: BUILD_ALPHA_051_WINDOWS.bat "D:\Epic Games\UE_5.8"
 exit /b 3
)
if not exist "%EDITOR%" (echo [ERROR] UnrealEditor.exe not found: "%EDITOR%" & exit /b 4)
where cl.exe >nul 2>&1
if errorlevel 1 echo [INFO] cl.exe not in PATH. UnrealBuildTool may still locate Visual Studio automatically.
echo [NYVERRA] Building editor target. Please check errors in BUILD_ALPHA_051_ERRORS.txt.
call "%BUILDER%" NYVERRAEditor Win64 Development -Project="%PROJECT%" -WaitMutex -NoHotReloadFromIDE > "%LOG%" 2>&1
set "RESULT=!ERRORLEVEL!"
py -3 "Tools\summarize_build_051.py" "%LOG%" "%ERRS%"
if errorlevel 1 echo [WARN] Summary unavailable. Full log: "%LOG%"
if not "!RESULT!"=="0" (
 echo [FAILED] Unreal editor build exited with !RESULT!.
 echo [DETAILS] "%LOG%"
 echo [ERRORS] "%ERRS%"
 exit /b !RESULT!
)
echo [SUCCESS] Unreal editor C++ target built.
echo [NOTE] This does not establish a playable map or multiplayer correctness.
exit /b 0
