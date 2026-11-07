@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (py -3 Tools\validate_alpha_035.py) else (python Tools\validate_alpha_035.py)
if errorlevel 1 (
 echo Preflight failed. Resolve the errors before building.
 exit /b 1
)
echo Preflight OK. Now compile using BUILD_ALPHA_033_WINDOWS.bat.
echo After opening Unreal Editor, run Tools\create_test_world.py if you do not have a map.
exit /b 0
