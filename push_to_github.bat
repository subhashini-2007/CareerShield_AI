@echo off
setlocal enabledelayedexpansion

echo ==========================================================
echo  CareerShield AI - GitHub Deployment Pipeline
echo ==========================================================
echo.

cd /d "C:\Users\subha\OneDrive\Desktop\CareerShield_AI"
if errorlevel 1 (
    echo [ERROR] Could not navigate to C:\Users\subha\OneDrive\Desktop\CareerShield_AI
    pause
    exit /b 1
)

echo [STEP 1/6] Verifying repository isolation...
for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set GIT_ROOT=%%i
if "%GIT_ROOT%"=="" (
    echo [INFO] Initializing Git repository...
    git init
    for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set GIT_ROOT=%%i
)
echo [PASS] Git root is: %GIT_ROOT%

echo.
echo [STEP 2/6] Unstaging backup files (preserving local original)...
git rm --cached backend/app/services/analyzer_service.py.bak 2>nul
echo [PASS] Backup file safely removed from Git index.

echo.
echo [STEP 3/6] Staging project files respecting .gitignore...
git add .
echo [PASS] Clean project files staged.

echo.
echo [STEP 4/6] Setting default branch to main...
git branch -M main

echo.
echo [STEP 5/6] Verifying remote origin...
git remote set-url origin https://github.com/subhashini-2007/CareerShield_AI.git 2>nul
if errorlevel 1 (
    git remote add origin https://github.com/subhashini-2007/CareerShield_AI.git
)
echo [PASS] Remote origin set to https://github.com/subhashini-2007/CareerShield_AI.git

echo.
echo [STEP 6/6] Creating initial commit and pushing to GitHub...
git commit -m "Initial commit: CareerShield AI"
echo.
echo Pushing to GitHub (if a browser login window opens, click 'Sign in with your browser')...
git push -u origin main

if errorlevel 1 (
    echo.
    echo [NOTE] Push did not complete. If a GitHub login window opened, please complete authentication.
    pause
    exit /b 1
)

echo.
echo ==========================================================
echo  SUCCESS: CareerShield AI is live on GitHub!
echo  URL: https://github.com/subhashini-2007/CareerShield_AI
echo ==========================================================
pause
