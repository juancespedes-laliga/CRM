import * as XLSX from 'xlsx'
import type { DestinatarioCampanaMT, DetalleCampanaMT } from '../types/mailerturbo'

// Resultados de MailerTurbo que significan que el correo NO llegó al buzón.
const RESULTADOS_NO_ENTREGADOS = new Set(['rebote', 'rechazado'])

/** true si el correo salió y no rebotó (una baja sí recibió el correo). */
export const fueEnviado = (d: DestinatarioCampanaMT) =>
  d.estadoEnvio.toLowerCase() === 'enviado' && !RESULTADOS_NO_ENTREGADOS.has(d.resultadoEnvio.toLowerCase())

/** Por qué no se le envió: Rebote / Rechazado, o el estado del envío (pendiente, cancelado…). */
export const motivoNoEnviado = (d: DestinatarioCampanaMT) =>
  d.estadoEnvio.toLowerCase() === 'enviado' ? d.resultadoEnvio : (d.estadoEnvio || 'Sin enviar')

export type FiltroDestinatarios = 'todos' | 'enviados' | 'no_enviados' | 'abrieron' | 'no_abrieron' | 'clic' | 'bajas'

export const FILTROS_DESTINATARIOS: { id: FiltroDestinatarios; label: string; cumple: (d: DestinatarioCampanaMT) => boolean }[] = [
  { id: 'todos', label: 'Todos', cumple: () => true },
  { id: 'enviados', label: 'Enviados', cumple: fueEnviado },
  { id: 'no_enviados', label: 'No enviados', cumple: d => !fueEnviado(d) },
  { id: 'abrieron', label: 'Abrieron', cumple: d => d.abrio },
  { id: 'no_abrieron', label: 'No abrieron', cumple: d => fueEnviado(d) && !d.abrio },
  { id: 'clic', label: 'Hicieron clic', cumple: d => d.clic },
  { id: 'bajas', label: 'Se dieron de baja', cumple: d => d.baja },
]

const siNo = (v: boolean) => (v ? 'Sí' : 'No')

const fila = (d: DestinatarioCampanaMT) => ({
  'Nombre': d.nombre,
  'Correo': d.correo,
  'Teléfono': d.telefono ?? '',
  '¿Enviado?': siNo(fueEnviado(d)),
  'Estado del envío': d.estadoEnvio,
  'Resultado': d.resultadoEnvio,
  'Fecha de envío': d.fechaEnviado ?? '',
  'Abrió': siNo(d.abrio),
  'Fecha de apertura': d.fechaApertura ?? '',
  'Hizo clic': siNo(d.clic),
  'Fecha del clic': d.fechaClic ?? '',
  'Links': d.links.join(' | '),
  'Se dio de baja': siNo(d.baja),
  'Fecha de baja': d.fechaBaja ?? '',
  'Vio la landing': siNo(d.vistaLanding),
})

const ANCHOS = [28, 32, 14, 10, 14, 12, 19, 8, 19, 10, 19, 40, 13, 19, 13].map(wch => ({ wch }))

function hoja(destinatarios: DestinatarioCampanaMT[]) {
  const h = XLSX.utils.json_to_sheet(destinatarios.map(fila))
  h['!cols'] = ANCHOS
  return h
}

const slug = (s: string) =>
  s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 40) || 'campana'

/** Libro con Resumen, Enviados, No enviados y Todos. Con `soloFiltro` exporta
 * únicamente esas filas (lo que se ve en la tabla) en una hoja. */
export function exportarDestinatariosExcel(
  campana: DetalleCampanaMT,
  destinatarios: DestinatarioCampanaMT[],
  soloFiltro?: { label: string; filas: DestinatarioCampanaMT[] },
): void {
  const libro = XLSX.utils.book_new()
  const fecha = new Date().toISOString().split('T')[0]

  if (soloFiltro) {
    XLSX.utils.book_append_sheet(libro, hoja(soloFiltro.filas), soloFiltro.label.slice(0, 31))
    XLSX.writeFile(libro, `campana_${campana.id}_${slug(campana.nombre)}_${slug(soloFiltro.label)}_${fecha}.xlsx`)
    return
  }

  const enviados = destinatarios.filter(fueEnviado)
  const noEnviados = destinatarios.filter(d => !fueEnviado(d))
  const pct = (n: number) => (destinatarios.length ? `${((n / destinatarios.length) * 100).toFixed(1)}%` : '0%')
  const abrieron = destinatarios.filter(d => d.abrio).length
  const clics = destinatarios.filter(d => d.clic).length
  const bajas = destinatarios.filter(d => d.baja).length

  const resumen = XLSX.utils.aoa_to_sheet([
    ['Campaña', campana.nombre],
    ['ID MailerTurbo', campana.id],
    ['Asunto', campana.asunto ?? ''],
    ['Estado', campana.estado],
    ['Fecha', campana.fecha ?? ''],
    ['Perfil de envío', [campana.perfilEnvio, campana.correoPerfilEnvio].filter(Boolean).join(' · ')],
    ['Listas', campana.listas ?? ''],
    ['Enviada por', campana.usuarioEnvio ?? ''],
    [],
    ['Indicador', 'Cantidad', '% del total'],
    ['Destinatarios', destinatarios.length, '100%'],
    ['Enviados', enviados.length, pct(enviados.length)],
    ['No enviados', noEnviados.length, pct(noEnviados.length)],
    ['Abrieron', abrieron, pct(abrieron)],
    ['Hicieron clic', clics, pct(clics)],
    ['Se dieron de baja', bajas, pct(bajas)],
  ])
  resumen['!cols'] = [{ wch: 20 }, { wch: 60 }, { wch: 12 }]

  XLSX.utils.book_append_sheet(libro, resumen, 'Resumen')
  XLSX.utils.book_append_sheet(libro, hoja(enviados), 'Enviados')
  XLSX.utils.book_append_sheet(libro, hoja(noEnviados), 'No enviados')
  XLSX.utils.book_append_sheet(libro, hoja(destinatarios), 'Todos')
  XLSX.writeFile(libro, `campana_${campana.id}_${slug(campana.nombre)}_${fecha}.xlsx`)
}
