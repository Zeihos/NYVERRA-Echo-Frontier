@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA Alpha 0.62 - Character save verification
echo ======================================================
echo NYVERRA 0.62 - Python regressions + UE5.8 Editor build
echo ======================================================
if not exist "NYVERRA.uproject" (
 echo [ERROR] Run this BAT from the NYVERRA checkout root.
 exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python 3 launcher "py" is missing.
 exit /b 3
)
echo [1/4] Check Python syntax...
py -3 -m compileall -q Tools
if errorlevel 1 (echo [ERROR] Python syntax failed.&exit /b 4)
echo [2/4] Check project layout, links and metadata...
py -3 Tools\check_repository.py
if errorlevel 1 (echo [ERROR] Project hygiene failed.&exit /b 5)
echo [3/4] Run source regression suite...
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
if errorlevel 1 (echo [ERROR] Offline regressions failed.&exit /b 6)
echo [4/4] Compile NYVERRAEditor with Unreal Engine 5.8...
call "%~dp0BUILD_ALPHA_051_WINDOWS.bat" "%~1"
if errorlevel 1 (
 echo [ERROR] Unreal Editor C++ build failed. Read BUILD_ALPHA_051_ERRORS.txt.
 exit /b 7
)
echo [SUCCESS] Offline regression suite and Unreal C++ Editor build finished.
echo [NEXT] Follow ALPHA_062_QA.md for Standalone/dedicated save and reconnect tests.
echo [NOTE] Compile success alone does not confirm real disk or network operation.
exit /b 0
