@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "REPO_URL=https://github.com/Zeihos/NYVERRA-Echo-Frontier.git"
if not "%~1"=="" set "REPO_URL=%~1"
where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git for Windows not installed or not in PATH.
  pause
  exit /b 3
)
echo.
echo [IMPORTANT] This script cannot verify that the remote GitHub repo is Private.
echo [IMPORTANT] BEFORE continuing, verify visibility=PRIVATE in GitHub repo Settings.
echo Remote: %REPO_URL%
choice /C YN /M "Have you verified repository visibility is PRIVATE?"
if errorlevel 2 exit /b 4
if not exist ".git" (
  git init -b main
  if errorlevel 1 goto :fail
)
git add -A
if errorlevel 1 goto :fail
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "Import NYVERRA Echo Frontier Alpha 0.52 and archived versions 0.1-0.52"
  if errorlevel 1 goto :fail
)
git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin "%REPO_URL%"
) else (
  git remote set-url origin "%REPO_URL%"
)
if errorlevel 1 goto :fail
git push -u origin main
if errorlevel 1 goto :fail
echo.
echo [SUCCESS] Pushed project to private repository (verify visibility in GitHub).
pause
exit /b 0
:fail
echo [ERROR] Upload failed. Review output above.
pause
exit /b 1
