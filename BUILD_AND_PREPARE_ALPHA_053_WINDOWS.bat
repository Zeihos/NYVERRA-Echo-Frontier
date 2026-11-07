@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "UE_ROOT=%~1"
if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "UE_CMD=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
set "PROJECT=%CD%\NYVERRA.uproject"
set "SCRIPT=%CD%\Tools\bootstrap_alpha_053.py"
set "LOG=%CD%\BUILD_ALPHA_053_MAP.log"

if not exist "%PROJECT%" (echo [ERROR] NYVERRA.uproject missing.& exit /b 2)
if not exist "%UE_CMD%" (echo [ERROR] Missing "%UE_CMD%" & exit /b 3)
if not exist "%SCRIPT%" (echo [ERROR] Missing "%SCRIPT%" & exit /b 4)

echo [1/3] Compiling NYVERRAEditor with Unreal Engine 5.8...
call "%CD%\BUILD_ALPHA_051_WINDOWS.bat" "%UE_ROOT%"
if errorlevel 1 (echo [ERROR] Compilation failed. See BUILD_ALPHA_051.log & exit /b 5)

echo [2/3] Bootstrapping persistent TestWorld via Unreal Editor Python...
echo [INFO] Existing TestWorld is preserved. See BUILD_ALPHA_053_MAP.log for details.
"%UE_CMD%" "%PROJECT%" -Unattended -NoSplash -ExecutePythonScript="%SCRIPT%" > "%LOG%" 2>&1
if errorlevel 1 (echo [ERROR] Unreal Editor map bootstrap failed. See "%LOG%" & exit /b 6)

echo [3/3] Verifying saved level and startup configuration...
if not exist "%CD%\Content\Maps\TestWorld.umap" (
 echo [ERROR] TestWorld.umap was not saved. Review "%LOG%"
 exit /b 7
)
findstr /B /C:"GameDefaultMap=/Game/Maps/TestWorld" "%CD%\Config\DefaultEngine.ini" >nul
if errorlevel 1 (echo [ERROR] GameDefaultMap not configured. See "%LOG%" & exit /b 8)
findstr /B /C:"EditorStartupMap=/Game/Maps/TestWorld" "%CD%\Config\DefaultEngine.ini" >nul
if errorlevel 1 (echo [ERROR] EditorStartupMap not configured. See "%LOG%" & exit /b 9)
findstr /B /C:"ServerDefaultMap=/Game/Maps/TestWorld" "%CD%\Config\DefaultEngine.ini" >nul
if errorlevel 1 (echo [ERROR] ServerDefaultMap not configured. See "%LOG%" & exit /b 10)

echo [SUCCESS] C++ editor target built and TestWorld saved/configured.
echo [NEXT] Open NYVERRA.uproject, Build Navigation, save map, run PIE 2 players.
echo [NOTE] This is NOT a complete playtest or packaged Windows build.
exit /b 0
