@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title NYVERRA Alpha 0.58 - Build and Raid Smoke Test

echo ============================================
echo NYVERRA: ECHO FRONTIER - ALPHA 0.58
echo ============================================
if not exist "NYVERRA.uproject" (
 echo [ERROR] Run in the NYVERRA Git clone next to NYVERRA.uproject
 exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python 3 launcher not available.
 exit /b 3
)
echo [1/3] Checking Python tools...
py -3 -m compileall -q Tools
if errorlevel 1 (echo [ERROR] Python syntax check failed.&exit /b 4)
echo [2/3] Running all offline regression checks...
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
if errorlevel 1 (echo [ERROR] Regression tests failed.&exit /b 5)
echo [3/3] Building UE5.8 NYVERRAEditor target...
call "BUILD_ALPHA_051_WINDOWS.bat" "%~1"
if errorlevel 1 (
 echo [ERROR] Unreal compilation failed. See BUILD_ALPHA_051_ERRORS.txt
 exit /b 6
)
echo [SUCCESS] Offline tests and local NYVERRAEditor build finished.
echo [NEXT] Open TestWorld, use PIE with 2 players. Check ALPHA_058_QA.md.
echo [NOTE] This script cannot validate runtime replication, raids or packaged builds.
exit /b 0
