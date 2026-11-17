@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "REPO_URL=https://github.com/Zeihos/NYVERRA-Echo-Frontier.git"

echo ==============================================
echo NYVERRA - RESUME PRIVATE GITHUB UPLOAD
 echo ==============================================
where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git for Windows not found.
  goto :fail
)
if not exist "NYVERRA.uproject" (
  echo [ERROR] Place this file next to NYVERRA.uproject.
  goto :fail
)
if not exist ".git" (
  echo [ERROR] Existing local Git repository not found.
  echo [INFO] This file resumes the previous failed push; do not re-extract the project over your files.
  goto :fail
)

echo [IMPORTANT] Target: %REPO_URL%
echo [IMPORTANT] Repository must be PRIVATE. It was confirmed Private through GitHub on 2026-11-07.
choice /C YN /M "Continue uploading to this PRIVATE repository?"
if errorlevel 2 exit /b 2

git config --local user.name "Zeihos"
if errorlevel 1 goto :fail
git config --local user.email "279975551+Zeihos@users.noreply.github.com"
if errorlevel 1 goto :fail

set /a HISTORY_COUNT=0
for %%F in ("History\UE5_Alpha_Archives\NYVERRA-UE5-Alpha-*-source.zip") do (
  if exist "%%~fF" set /a HISTORY_COUNT+=1
)
echo.
echo [INFO] Previous alpha ZIP archives found: %HISTORY_COUNT% of 52
if not "%HISTORY_COUNT%"=="52" (
  echo [WARNING] Missing some ZIP archives from History\UE5_Alpha_Archives.
  echo [WARNING] To upload ALL versions, first extract history parts 02-07 into this same project folder.
  choice /C YN /M "Upload anyway without the missing archives?"
  if errorlevel 2 exit /b 3
)

echo.
echo [INFO] Staging all current project files...
git add -A
if errorlevel 1 goto :fail
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "Complete NYVERRA source and history import"
  if errorlevel 1 goto :fail
)

git rev-parse --verify HEAD >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git commit not found.
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
echo [INFO] Uploading current HEAD to GitHub main (without force)...
git push -u origin HEAD:refs/heads/main
if errorlevel 1 goto :fail

echo.
echo [SUCCESS] GitHub upload completed.
echo [INFO] Verify repository files at: https://github.com/Zeihos/NYVERRA-Echo-Frontier
pause
exit /b 0

:fail
echo.
echo [ERROR] GitHub upload not completed. Copy the error lines above into ChatGPT.
pause
exit /b 1
