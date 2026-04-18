# Script de Despliegue Global para Microservicios del Banco
# Este script automatiza el terraform init y terraform apply en todos los servicios.

$services = @(
    "d:\bank-user-service",
    "d:\bank-payment-service",
    "d:\bank-card-transaction-service",
    "d:\Notification Service"
)

Write-Host "Iniciando despliegue global de infraestructura..." -ForegroundColor Cyan

foreach ($service in $services) {
    if (Test-Path "$service\terraform") {
        Write-Host "`n>>> Procesando: $service" -ForegroundColor Yellow
        Push-Location "$service\terraform"
        
        Write-Host "Ejecutando terraform init..."
        terraform init -input=false
        
        Write-Host "Ejecutando terraform apply..."
        terraform apply -auto-approve -input=false
        
        Pop-Location
    } else {
        Write-Warning "No se encontró carpeta de terraform en $service"
    }
}

Write-Host "`n¡Despliegue global completado con éxito!" -ForegroundColor Green
