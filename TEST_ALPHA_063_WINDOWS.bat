@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title NYVERRA Alpha 0.63 - Medical Survival
echo ========================================================
echo NYVERRA Alpha 0.63 - offline tests and UE5.8 Editor build
echo ========================================================
if not exist "NYVERRA.uproject" (
 echo [ERROR] Run from the folder containing NYVERRA.uproject.
 exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
 echo [ERROR] Python 3 launcher "py" not installed.
 exit /b 3
)
echo [1/4] Validate Python source...
py -3 -m compileall -q Tools
if errorlevel 1 (echo [ERROR] Python syntax check failed.&exit /b 4)
echo [2/4] Validate project metadata and links...
py -3 Tools\check_repository.py
if errorlevel 1 (echo [ERROR] Repository check failed.&exit /b 5)
echo [3/4] Run all Alpha source regression checks...
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
if errorlevel 1 (echo [ERROR] Python source tests failed.&exit /b 6)
echo [INFO] Checking playable map readiness (report only)...
py -3 Tools\check_runtime_readiness.py
if errorlevel 1 (echo [ERROR] Runtime readiness diagnostic failed.&exit /b 8)
echo [4/4] Build UE 5.8 NYVERRAEditor...
call "%~dp0BUILD_ALPHA_051_WINDOWS.bat" "%~1"
if errorlevel 1 (
 echo [ERROR] C++ compilation failed. Check BUILD_ALPHA_051_ERRORS.txt.
 exit /b 7
)
echo [SUCCESS] Source checks and UE Editor C++ build completed.
echo [NEXT] Check ALPHA_063_QA.md for two-player tests and medical survival.
echo [NOTE] Unreal gameplay/packaging require manual validation.
exit /b 0
