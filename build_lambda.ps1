# Script para construir el paquete de despliegue de Lambda compatible con Linux (desde Windows)
# Este script descarga las ruedas (wheels) de Linux para asegurar que libreras como bcrypt funcionen.

param (
    [string]$ServiceDir = "d:\bank-user-service",
    [string]$OutputDir = "d:\bank-user-service\terraform\user_service.zip"
)

Write-Host ">>> Construyendo paquete de despliegue para: $ServiceDir" -ForegroundColor Cyan

$TempDir = Join-Path $ServiceDir "deployment_package"
if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
New-Item -ItemType Directory -Path $TempDir

# 1. Instalar dependencias para Linux x86_64 y Python 3.13
Write-Host "Instando dependencias compatibles con Linux..."
pip install -r "$ServiceDir\requirements.txt" `
    --target $TempDir `
    --platform manylinux2014_x86_64 `
    --only-binary=:all: `
    --implementation cp `
    --python-version 3.13 `
    --upgrade

# 2. Copiar cdigo fuente del microservicio
Write-Host "Copiando cdigo fuente y archivos __init__.py..."
Copy-Item -Recurse "$ServiceDir\app" $TempDir
Copy-Item -Recurse "$ServiceDir\lambdas" $TempDir

# 3. Empaquetar en ZIP
Write-Host "Creando archivo ZIP..."
if (Test-Path $OutputDir) { Remove-Item -Force $OutputDir }
Compress-Archive -Path "$TempDir\*" -DestinationPath $OutputDir -Force

Write-Host ">>> Paquete creado exitosamente: $OutputDir" -ForegroundColor Green
