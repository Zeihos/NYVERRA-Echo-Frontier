@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA Alpha 0.60 - Base Persistence

echo =====================================================
echo NYVERRA Alpha 0.60 - WORLD SAVE REGRESSION / UE BUILD
echo =====================================================
if not exist "NYVERRA.uproject" (
 echo [ERROR] Run this script in the NYVERRA Git clone.
 exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python 3 launcher not available.
 exit /b 3
)
echo [1/3] Validating Python source...
py -3 -m compileall -q Tools
if errorlevel 1 (echo [ERROR] Python syntax validation failed.&exit /b 4)
echo [2/3] Running full offline regression suite...
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
if errorlevel 1 (echo [ERROR] Offline regression tests failed.&exit /b 5)
echo [3/3] Compiling NYVERRAEditor with Unreal Engine 5.8...
call "BUILD_ALPHA_051_WINDOWS.bat" "%~1"
if errorlevel 1 (
 echo [ERROR] Unreal Editor compilation failed.
 echo [LOG] BUILD_ALPHA_051.log and BUILD_ALPHA_051_ERRORS.txt
 exit /b 6
)
echo [SUCCESS] Offline checks and local UE5.8 Editor build completed.
echo [NEXT] Follow ALPHA_060_QA.md to test persistence in STANDALONE, NOT PIE.
echo [NOTE] This BAT does NOT prove saving or 2-player server persistence.
exit /b 0
