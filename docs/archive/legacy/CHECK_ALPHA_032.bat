@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
 py -3 Tools\validate_alpha_032.py
) else (
 python Tools\validate_alpha_032.py
)
if errorlevel 1 (echo Offline validation FAILED.) else (echo Offline validation PASSED. Unreal Engine build still required.)
pause
