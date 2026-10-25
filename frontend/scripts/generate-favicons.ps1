# CareerShield AI — Favicon & Apple Touch Icon Generator
# Converts the uploaded high-res CareerShield AI logo into crisp 32x32 and 180x180 icons

Add-Type -AssemblyName System.Drawing

$sourcePath = "C:\Users\subha\.gemini\antigravity\brain\bec347bd-bd66-4232-80cd-243714b48d77\.user_uploaded\media_1792912047506_e6c0b78b.png"
$rootDir = (Get-Item $PSScriptRoot).Parent.FullName
$appDir = Join-Path $rootDir "src\app"
$publicDir = Join-Path $rootDir "public"

if (-not (Test-Path $sourcePath)) {
    Write-Error "Source image not found at $sourcePath"
    exit 1
}

# Ensure destination directories exist
if (-not (Test-Path $appDir)) {
    New-Item -ItemType Directory -Path $appDir -Force | Out-Null
}
if (-not (Test-Path $publicDir)) {
    New-Item -ItemType Directory -Path $publicDir -Force | Out-Null
}

$img = [System.Drawing.Image]::FromFile($sourcePath)

try {
    # 1. Generate crisp 32x32 PNG favicon for Next.js App Router (src/app/icon.png)
    $bmp32 = New-Object System.Drawing.Bitmap(32, 32)
    $g32 = [System.Drawing.Graphics]::FromImage($bmp32)
    $g32.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g32.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g32.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g32.Clear([System.Drawing.Color]::Transparent)
    $g32.DrawImage($img, 0, 0, 32, 32)
    
    $iconPath = Join-Path $appDir "icon.png"
    $bmp32.Save($iconPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g32.Dispose()
    $bmp32.Dispose()

    # 2. Generate 180x180 PNG Apple Touch Icon for Next.js App Router (src/app/apple-icon.png)
    $bmp180 = New-Object System.Drawing.Bitmap(180, 180)
    $g180 = [System.Drawing.Graphics]::FromImage($bmp180)
    $g180.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g180.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g180.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g180.Clear([System.Drawing.Color]::Transparent)
    $g180.DrawImage($img, 0, 0, 180, 180)
    
    $appleIconPath = Join-Path $appDir "apple-icon.png"
    $bmp180.Save($appleIconPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g180.Dispose()
    $bmp180.Dispose()

    # 3. Also copy to public/favicon.ico as browser fallback
    $fallbackIco = Join-Path $publicDir "favicon.ico"
    Copy-Item $iconPath $fallbackIco -Force

    Write-Host "Favicons generated successfully:" -ForegroundColor Green
    Write-Host " [x] App Router Icon:       $iconPath (32x32 PNG)"
    Write-Host " [x] Apple Touch Icon:      $appleIconPath (180x180 PNG)"
    Write-Host " [x] Legacy Fallback:       $fallbackIco"
}
finally {
    $img.Dispose()
}
