@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA - Alpha 0.57 validation

echo =========================================================
echo NYVERRA Alpha 0.57 - Offline checks + UE 5.8 C++ build
echo =========================================================
if not exist "NYVERRA.uproject" (
 echo [ERROR] NYVERRA.uproject is missing; run this in project root.
 exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python launcher 'py -3' is unavailable.
 exit /b 3
)
echo [1/3] Python script syntax check...
py -3 -m compileall -q Tools
if errorlevel 1 (
 echo [ERROR] Python syntax check failed.
 exit /b 4
)
echo [2/3] Running source regression suite...
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
if errorlevel 1 (
 echo [ERROR] Offline tests failed. Fix code before compiling.
 exit /b 5
)
echo [3/3] Building NYVERRAEditor (requires installed Unreal Engine 5.8)...
call "BUILD_ALPHA_051_WINDOWS.bat" "%~1"
if errorlevel 1 (
 echo [ERROR] UE C++ compilation failed; inspect BUILD_ALPHA_051.log
 exit /b 6
)
echo [SUCCESS] Offline checks and local UE C++ editor build completed.
echo [NEXT] Run manual two-player PIE checks from ALPHA_057_QA.md.
echo [NOTE] A successful compile is NOT a packaged release or multiplayer QA.
exit /b 0
