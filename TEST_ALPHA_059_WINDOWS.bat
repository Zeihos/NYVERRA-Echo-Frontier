@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA Alpha 0.59 - Doors and Raids

echo ====================================================
echo NYVERRA Alpha 0.59 - source checks and UE5.8 build
echo ====================================================
if not exist "NYVERRA.uproject" (
 echo [ERROR] Run this inside your Git clone with NYVERRA.uproject.
 exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python 3 launcher missing.
 exit /b 3
)
echo [1/3] Python syntax check...
py -3 -m compileall -q Tools
if errorlevel 1 (echo [ERROR] Syntax check failed.& exit /b 4)
echo [2/3] Complete offline regression suite...
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
if errorlevel 1 (echo [ERROR] Offline tests failed.& exit /b 5)
echo [3/3] Building NYVERRAEditor...
call "BUILD_ALPHA_051_WINDOWS.bat" "%~1"
if errorlevel 1 (
 echo [ERROR] UE C++ build failed; see BUILD_ALPHA_051_ERRORS.txt
 exit /b 6
)
echo [SUCCESS] Offline checks and Unreal Editor C++ build completed.
echo [NEXT] Follow ALPHA_059_QA.md for the 2-player locked door test.
echo [NOTE] Neither PIE multiplayer nor Windows shipping package was tested.
exit /b 0
