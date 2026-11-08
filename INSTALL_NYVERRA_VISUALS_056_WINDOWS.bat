@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title NYVERRA - VISUAL POLISH 0.56

set "UE_ROOT=%~1"
if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "BUILDER=%UE_ROOT%\Engine\Build\BatchFiles\Build.bat"
set "EDITOR_CMD=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
set "PROJECT=%CD%\NYVERRA.uproject"
set "SCRIPT=%CD%\Tools\finalize_visual_polish_056.py"
set "LOG=%CD%\VISUAL_POLISH_056_UNREAL.log"
set "ASSETS=%CD%\Content\NYVERRA\VisualPolish"
set "MAP=%CD%\Content\Maps\TestWorld_Visual056.umap"

echo ====================================================
echo NYVERRA - VISUAL POLISH 0.56 - PRIVATE SOURCE PROJECT
echo ====================================================
if not exist "%PROJECT%" (
 echo [ERROR] Place this BAT beside NYVERRA.uproject in the Git clone.
 exit /b 2
)
if not exist "%SCRIPT%" (
 echo [ERROR] Missing Tools\finalize_visual_polish_056.py
 echo [ACTION] git pull origin main
 exit /b 3
)
if not exist "%CD%\Content\VisualPolishSource\Terrain\T_NyGrass_Albedo.png" (
 echo [ERROR] Extract the visual texture ZIP here before launching.
 exit /b 4
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python launcher not found. Install Python 3.
 exit /b 5
)
echo [1/5] Validating all textures and optional SHA256 manifest...
py -3 "Tools\validate_visual_pack_056.py"
if errorlevel 1 (
 echo [ERROR] Incomplete or corrupt texture pack. Unreal project unchanged.
 exit /b 6
)
if not exist "%BUILDER%" (
 echo [ERROR] Unreal Engine 5.8 not found at "%UE_ROOT%"
 echo Usage: INSTALL_NYVERRA_VISUALS_056_WINDOWS.bat "D:\Epic Games\UE_5.8"
 exit /b 7
)
if not exist "%EDITOR_CMD%" (
 echo [ERROR] UnrealEditor-Cmd.exe not found. Check UE_ROOT.
 exit /b 8
)
echo [2/5] Building NYVERRAEditor...
call "BUILD_ALPHA_051_WINDOWS.bat" "%UE_ROOT%"
if errorlevel 1 (
 echo [ERROR] C++ build failed. See BUILD_ALPHA_051.log / BUILD_ALPHA_051_ERRORS.txt
 exit /b 9
)
echo [3/5] Importing PBR materials and safely creating TestWorld_Visual056...
echo [INFO] Original TestWorld will NOT be overwritten.
"%EDITOR_CMD%" "%PROJECT%" -Unattended -NoSplash -ExecutePythonScript="%SCRIPT%" > "%LOG%" 2>&1
if errorlevel 1 (
 echo [ERROR] Unreal import/map creation failed; see "%LOG%"
 exit /b 10
)
echo [4/5] Verifying saved generated Unreal assets...
if not exist "%MAP%" (
 echo [ERROR] Visual map missing: "%MAP%"
 echo [LOG] "%LOG%"
 exit /b 11
)
if not exist "%ASSETS%\Materials\M_NyLandscape_PBR055.uasset" (
 echo [ERROR] Unreal PBR Landscape material missing. See "%LOG%"
 exit /b 12
)
if not exist "%ASSETS%\Textures\T_NyGrass_Albedo.uasset" (
 echo [ERROR] Grass texture did not import. See "%LOG%"
 exit /b 13
)
echo [5/5] Completed. Your authored TestWorld was preserved.
echo [SUCCESS] New level: Content\Maps\TestWorld_Visual056.umap
echo [SUCCESS] Material: Content\NYVERRA\VisualPolish\Materials\M_NyLandscape_PBR055.uasset
echo [NOTE] You must open the visual map in Unreal Editor and inspect appearance,
echo [NOTE] lighting, shader compilation, NavMesh, gameplay and frame rate.
echo.
choice /C YN /M "Upload generated texture PNGs, Unreal assets and Visual056 map to PRIVATE GitHub now"
if errorlevel 2 goto :end
powershell -NoProfile -ExecutionPolicy Bypass -File "Tools\Sync-VisualPolish-ToGitHub.ps1" -WithImportedAssets
if errorlevel 1 (
 echo [ERROR] GitHub upload failed. Local materials and map remain safe.
 exit /b 14
)
echo [SUCCESS] PBR assets and visual test map pushed to PRIVATE repository.
:end
echo [INFO] Finished. Close this window or press a key.
exit /b 0
