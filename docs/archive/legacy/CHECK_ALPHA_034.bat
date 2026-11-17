@echo off
setlocal
cd /d "%~dp0"
py -3 Tools\check_source_034.py
if errorlevel 1 (
 echo Alpha 0.34 offline check FAILED
 exit /b 1
)
echo Alpha 0.34 offline check PASSED. Unreal compilation still required.
endlocal
