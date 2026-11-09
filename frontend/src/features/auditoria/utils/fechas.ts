import { DIAS_POR_VENCER } from '../constants/auditoria.constants'
import type { VigenciaRenovacion } from '../types/auditoria'

const aFecha = (v: string) => new Date(v.length === 10 ? `${v}T00:00:00` : v)

/** 'AAAA-MM-DD' → '05/11/2026'. */
export function formatoFecha(v: string | null | undefined): string {
  if (!v) return '—'
  return aFecha(v).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

/** ISO con hora → '05/11/2026 14:32'. */
export function formatoFechaHora(v: string | null | undefined): string {
  if (!v) return '—'
  const d = aFecha(v)
  const fecha = d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
  const hora = d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false })
  return `${fecha} ${hora}`
}

/** ISO con hora → '14:32'. */
export function formatoHora(v: string | null | undefined): string {
  if (!v) return ''
  return aFecha(v).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false })
}

export function hoyISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Días desde hoy hasta la fecha (negativo si ya pasó). */
export function diasHasta(fecha: string): number {
  const hoy = aFecha(hoyISO()).getTime()
  return Math.round((aFecha(fecha).getTime() - hoy) / 86_400_000)
}

export function vigenciaDe(vencimiento: string): VigenciaRenovacion {
  const dias = diasHasta(vencimiento)
  if (dias < 0) return 'vencido'
  if (dias <= DIAS_POR_VENCER) return 'por_vencer'
  return 'vigente'
}

export function textoDiasRestantes(vencimiento: string): string {
  const dias = diasHasta(vencimiento)
  if (dias === 0) return 'Vence hoy'
  if (dias === 1) return 'Falta 1 día'
  if (dias > 0) return `Faltan ${dias} días`
  if (dias === -1) return 'Venció hace 1 día'
  return `Venció hace ${-dias} días`
}
