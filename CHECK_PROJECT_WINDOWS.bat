@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 Tools\preflight_030.py
) else (
  python Tools\preflight_030.py
)
pause
