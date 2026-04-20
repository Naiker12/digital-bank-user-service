$ErrorActionPreference = "Continue"

Write-Host "=== Building User Service Lambda ZIP ==="

$ProjectRoot = "D:\bank-user-service"

$BuildDir = Join-Path $ProjectRoot "lambda_build"
$ZipPath  = Join-Path $ProjectRoot "terraform\user_service.zip"

#  Clean previous build
if (Test-Path $BuildDir) {
    Write-Host "Cleaning previous build..."
    Remove-Item -Recurse -Force $BuildDir
}
New-Item -ItemType Directory -Path $BuildDir | Out-Null

#  Install ONLY bcrypt with Linux binaries (the critical one with C extensions)
Write-Host "Installing bcrypt for Linux platform..."
pip install bcrypt -t $BuildDir --no-cache-dir --platform manylinux2014_x86_64 --only-binary=:all: --implementation cp --python-version 3.13 2>&1 | Write-Host

#  Install all other (pure Python) dependencies normally
Write-Host "Installing pure Python dependencies..."
pip install PyJWT pydantic email-validator python-dotenv python-multipart -t $BuildDir --no-cache-dir 2>&1 | Write-Host

#  Remove passlib if it got pulled in
Get-ChildItem -Path $BuildDir -Directory -Filter "passlib*" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Removing leftover passlib: $($_.Name)"
    Remove-Item -Recurse -Force $_.FullName
}

#  Copy application code
Write-Host "Copying application code..."
Copy-Item -Recurse -Force (Join-Path $ProjectRoot "app") (Join-Path $BuildDir "app")
Copy-Item -Recurse -Force (Join-Path $ProjectRoot "lambdas") (Join-Path $BuildDir "lambdas")

#  Verify bcrypt is Linux binary
Write-Host "--- Verifying bcrypt binary ---"
$bcryptFiles = Get-ChildItem -Path $BuildDir -Recurse -Filter "_bcrypt*" -ErrorAction SilentlyContinue
if ($bcryptFiles) {
    foreach ($f in $bcryptFiles) { Write-Host "  Found: $($f.FullName)" }
} else {
    Write-Host "  WARNING: No _bcrypt binary found! Lambda will fail."
}

#  Create ZIP
Write-Host "Creating ZIP at: $ZipPath"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path "$BuildDir\*" -DestinationPath $ZipPath -Force

#  Report
$zipSize = (Get-Item $ZipPath).Length / 1MB
Write-Host "=== Build complete! ZIP size: $([math]::Round($zipSize, 2)) MB ==="
