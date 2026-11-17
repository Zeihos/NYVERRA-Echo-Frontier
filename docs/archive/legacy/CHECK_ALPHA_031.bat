@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 Tools\validate_release_031.py
) else (
  python Tools\validate_release_031.py
)
echo.
echo This only checks source files and data. Unreal Editor must compile the game.
pause
