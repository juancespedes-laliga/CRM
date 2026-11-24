// Descarga un Blob (ej. el Excel que arma el backend) con el nombre indicado.
// El enlace se agrega al documento antes del click (Firefox/Edge lo exigen) y la
// URL temporal se libera con un retraso: si se revoca justo después del click,
// el navegador a veces cancela la descarga sin mostrar ningún error.
export function descargarBlob(blob: Blob, nombreArchivo: string): void {
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreArchivo
  enlace.style.display = 'none'
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
