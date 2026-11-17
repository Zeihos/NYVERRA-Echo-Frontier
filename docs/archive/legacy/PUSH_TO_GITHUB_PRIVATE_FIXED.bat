@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "REPO_URL=https://github.com/Zeihos/NYVERRA-Echo-Frontier.git"
if not "%~1"=="" set "REPO_URL=%~1"

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git for Windows was not found in PATH.
  pause
  exit /b 3
)

if not exist "NYVERRA.uproject" (
  echo [ERROR] Place this BAT file in the NYVERRA project root, next to NYVERRA.uproject.
  pause
  exit /b 2
)

echo.
echo [IMPORTANT] Check that %REPO_URL% is PRIVATE in GitHub Settings.
choice /C YN /M "Have you confirmed this GitHub repository is PRIVATE?"
if errorlevel 2 exit /b 4

if not exist ".git" (
  git init -b main
  if errorlevel 1 goto :fail
)

rem Set author identity for THIS repo only; do not change global Git settings.
git config --local user.name "Zeihos"
if errorlevel 1 goto :fail
git config --local user.email "279975551+Zeihos@users.noreply.github.com"
if errorlevel 1 goto :fail

git add -A
if errorlevel 1 goto :fail
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "Import NYVERRA Echo Frontier Alpha 0.52 and history"
  if errorlevel 1 goto :fail
)

git branch --show-current | findstr /X /C:"main" >nul
if errorlevel 1 (
  echo [ERROR] Expected main branch. No changes made to existing branches.
  goto :fail
)

git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin "%REPO_URL%"
) else (
  git remote set-url origin "%REPO_URL%"
)
if errorlevel 1 goto :fail

echo.
echo [INFO] Pushing to %REPO_URL% ...
git push -u origin main
if errorlevel 1 goto :fail

echo.
echo [SUCCESS] Git push completed. Confirm contents and visibility on GitHub.
pause
exit /b 0

:fail
echo.
echo [ERROR] Upload failed. Review the Git error lines above.
pause
exit /b 1
