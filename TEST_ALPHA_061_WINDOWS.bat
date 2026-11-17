@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA Alpha 0.61 - A/B Save Validation

echo ======================================================
echo NYVERRA Alpha 0.61 - rotating server save regression
echo ======================================================
if not exist "NYVERRA.uproject" (
 echo [ERROR] Open this BAT in the NYVERRA project Git checkout.
 exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python 3 launcher py not found.
 exit /b 3
)
echo [1/3] Python syntax...
py -3 -m compileall -q Tools
if errorlevel 1 (echo [ERROR] Python syntax failed.&exit /b 4)
echo [2/3] Full offline regression suite...
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
if errorlevel 1 (echo [ERROR] Source regression failed.&exit /b 5)
echo [3/3] Compiling UE 5.8 NYVERRAEditor...
call "BUILD_ALPHA_051_WINDOWS.bat" "%~1"
if errorlevel 1 (
 echo [ERROR] C++ build failed. Inspect BUILD_ALPHA_051_ERRORS.txt
 exit /b 6
)
echo [SUCCESS] Offline suite and local Unreal Editor build succeeded.
echo [NEXT] Follow ALPHA_061_QA.md for real save/restart/fallback verification.
echo [NOTE] These steps alone do NOT prove A/B recovery works in a game.
exit /b 0
