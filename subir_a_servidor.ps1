<#
  Sube la carpeta CRM completa a la carpeta compartida del servidor, lo mas rapido
  posible segun la capacidad de esta maquina (robocopy multihilo, un hilo por cada
  
  Uso: clic derecho sobre este archivo -> "Ejecutar con PowerShell",
       o desde una terminal parado en esta carpeta: .\subir_a_servidor.ps1
#>

$origen = $PSScriptRoot
$base   = "\\160.1.1.230\Sistemas\Juan David\APLICACIONES_SERVIDOR_160.2.1.22"
$destino = Join-Path $base (Split-Path $origen -Leaf)   # -> ...\APLICACIONES_SERVIDOR_160.2.1.22\CRM

# Hilos de copia = numero de procesadores logicos de esta maquina (32 es el tope que
# soporta robocopy): a mas nucleos, mas rapido sube, sin tener que ajustarlo a mano.
$hilos = [Math]::Min([Environment]::ProcessorCount, 32)

Write-Host "Origen : $origen"
Write-Host "Destino: $destino"
Write-Host "Hilos  : $hilos"
Write-Host ""

# Chequeo blando de la carpeta compartida: Test-Path sobre UNC a veces da
# falso negativo si la sesion SMB se durmio, asi que se reintenta y, si aun
# asi falla, solo se avisa (robocopy reintenta por su cuenta con /R /W).
$accesible = $false
for ($i = 1; $i -le 3 -and -not $accesible; $i++) {
    if (Test-Path -LiteralPath $base) { $accesible = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $accesible) {
    Write-Host "Aviso: no se pudo confirmar acceso a la carpeta base todavia:" -ForegroundColor Yellow
    Write-Host "  $base" -ForegroundColor Yellow
    Write-Host "Se intenta la copia de todos modos; si la ruta esta caida, robocopy fallara." -ForegroundColor Yellow
    Write-Host ""
}

robocopy $origen $destino /MIR /MT:$hilos /R:2 /W:5 `
  /XD node_modules venv .venv .git __pycache__ dist build .vite `
  /XF *.pyc *.log `
  /NFL /NDL

$codigo = $LASTEXITCODE
if ($codigo -lt 8) {
    Write-Host ""
    Write-Host "Listo, subida completa (codigo robocopy: $codigo)." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Hubo errores en la copia (codigo robocopy: $codigo). Revisa el detalle de arriba." -ForegroundColor Red
}
