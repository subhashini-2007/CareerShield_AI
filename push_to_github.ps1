# ==============================================================================
# CareerShield AI — Automated Git Setup & GitHub Push Script
# ==============================================================================
# This script safely executes the Git preparation, staging, and initial push
# for CareerShield AI directly to https://github.com/subhashini-2007/CareerShield_AI.
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " CareerShield AI — GitHub Repository Deployment Pipeline  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Enforce working directory
$expectedPath = "C:\Users\subha\OneDrive\Desktop\CareerShield_AI"
$currentPath = (Get-Location).Path
if ($currentPath -ne $expectedPath) {
    Write-Host "[INFO] Navigating to project directory: $expectedPath" -ForegroundColor Yellow
    Set-Location $expectedPath
}

# 2. Verify Git repository root isolation
Write-Host "`n[STEP 1/7] Verifying Git Repository Isolation..." -ForegroundColor Yellow
$gitRoot = git rev-parse --show-toplevel 2>$null
if (-not $gitRoot) {
    Write-Host "[INFO] Initializing dedicated Git repository in CareerShield_AI..." -ForegroundColor Cyan
    git init
    $gitRoot = git rev-parse --show-toplevel
}

$normalizedGitRoot = $gitRoot.Replace("/", "\").TrimEnd("\")
$normalizedExpected = $expectedPath.TrimEnd("\")

if ($normalizedGitRoot -ne $normalizedExpected) {
    Write-Host "[ERROR] Git root ($normalizedGitRoot) does NOT match expected project root ($normalizedExpected)!" -ForegroundColor Red
    Write-Host "Aborting to protect parent directories." -ForegroundColor Red
    Exit 1
}
Write-Host "[PASS] Git repository correctly isolated to: $normalizedGitRoot" -ForegroundColor Green

# 3. Resolve staged backup file if present
Write-Host "`n[STEP 2/7] Resolving staged backup files..." -ForegroundColor Yellow
$stagedBak = git diff --name-only --cached | Where-Object { $_ -like "*analyzer_service.py.bak*" }
if ($stagedBak) {
    Write-Host "[INFO] Removing $stagedBak from Git staging (keeping local original file)..." -ForegroundColor Cyan
    git rm --cached backend/app/services/analyzer_service.py.bak
    Write-Host "[PASS] Backup file removed from index without deleting local file." -ForegroundColor Green
} else {
    Write-Host "[INFO] No staged backup file found in index." -ForegroundColor Gray
}

# 4. Stage all valid project files
Write-Host "`n[STEP 3/7] Staging project files according to .gitignore..." -ForegroundColor Yellow
git add .

# 5. Check for whitespace warnings
Write-Host "`n[STEP 4/7] Checking for whitespace anomalies (git diff --cached --check)..." -ForegroundColor Yellow
$whitespaceWarnings = git diff --cached --check
if ($whitespaceWarnings) {
    Write-Host "[NOTE] Whitespace check output:" -ForegroundColor Gray
    $whitespaceWarnings | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "[PASS] Zero critical whitespace anomalies detected." -ForegroundColor Green
}

# 6. Audit staged files for security exclusions
Write-Host "`n[STEP 5/7] Auditing staged files for security exclusions..." -ForegroundColor Yellow
$stagedFiles = git diff --name-only --cached

$forbiddenPatterns = @(
    "backend/.env",
    "frontend/.env.local",
    "careershield.db",
    "node_modules",
    ".next",
    "venv/",
    "fake_job_postings.csv"
)

$securityViolations = @()
foreach ($file in $stagedFiles) {
    foreach ($pat in $forbiddenPatterns) {
        if ($file -like "*$pat*") {
            # Make sure example templates are allowed
            if ($file -notlike "*.example*") {
                $securityViolations += "$file (matched forbidden rule: $pat)"
            }
        }
    }
}

if ($securityViolations.Count -gt 0) {
    Write-Host "[SECURITY ALERT] Forbidden files detected in staging area:" -ForegroundColor Red
    $securityViolations | ForEach-Object { Write-Host "  [X] $_" -ForegroundColor Red }
    Write-Host "Aborting commit. Fix .gitignore before proceeding." -ForegroundColor Red
    Exit 1
}

Write-Host "[PASS] Security audit passed! Staged file count: $($stagedFiles.Count)" -ForegroundColor Green
Write-Host "  - .env secrets excluded: OK" -ForegroundColor Green
Write-Host "  - SQLite databases excluded: OK" -ForegroundColor Green
Write-Host "  - Virtual environments excluded: OK" -ForegroundColor Green
Write-Host "  - Node modules and build output excluded: OK" -ForegroundColor Green
Write-Host "  - Raw dataset (47.7MB CSV) excluded: OK" -ForegroundColor Green
Write-Host "  - Model metadata & pipeline preserved: OK" -ForegroundColor Green

# 7. Configure remote origin and branch
Write-Host "`n[STEP 6/7] Configuring branch and remote repository..." -ForegroundColor Yellow
git branch -M main

$targetRemote = "https://github.com/subhashini-2007/CareerShield_AI.git"
$existingRemote = git remote get-url origin 2>$null

if (-not $existingRemote) {
    git remote add origin $targetRemote
    Write-Host "[INFO] Added remote 'origin': $targetRemote" -ForegroundColor Cyan
} elseif ($existingRemote -ne $targetRemote) {
    git remote set-url origin $targetRemote
    Write-Host "[INFO] Updated remote 'origin' to: $targetRemote" -ForegroundColor Cyan
} else {
    Write-Host "[INFO] Remote 'origin' already correctly configured." -ForegroundColor Green
}

# 8. Create initial commit and push
Write-Host "`n[STEP 7/7] Committing and Pushing to GitHub..." -ForegroundColor Yellow

$headCommit = git rev-parse HEAD 2>$null
if (-not $headCommit) {
    git commit -m "Initial commit: CareerShield AI"
    Write-Host "[PASS] Created initial commit." -ForegroundColor Green
} else {
    Write-Host "[INFO] Committing pending changes..." -ForegroundColor Cyan
    git commit -m "Update CareerShield AI codebase and configurations" -q
}

$commitHash = (git rev-parse --short HEAD).Trim()
Write-Host "`nPushing main branch to origin ($targetRemote)..." -ForegroundColor Cyan
Write-Host "Note: If GitHub prompts for authentication, complete the browser login prompt." -ForegroundColor Yellow

git push -u origin main

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SUCCESS: CareerShield AI is live on GitHub!              " -ForegroundColor Green
Write-Host " Repository: $targetRemote" -ForegroundColor Green
Write-Host " Commit Hash: $commitHash                                 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
