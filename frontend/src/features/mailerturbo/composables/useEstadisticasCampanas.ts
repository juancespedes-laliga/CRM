import { computed, ref } from 'vue'
import type { CampanaMT } from '../types/mailerturbo'
import { getTodasLasCampanas } from '../services/mailerturbo.api'

// Estado compartido de la vista Estadísticas (sus pestañas leen lo mismo).
// Las tasas son PONDERADAS (total de aperturas / total de envíos), con la misma base
// que usa MailerTurbo: los envíos. Así una campaña de 2 correos no pesa igual que
// una de 5.000. La distribución (histograma, cajas) sí usa la tasa de cada campaña.

export interface CampanaFechada extends CampanaMT {
  f: Date
  anio: number
  /** 0 = enero. */
  mes: number
  dia: number
}

export interface Totales { campanas: number; envios: number; vistas: number; clicks: number; rebotes: number; salidas: number }
export type Metrica = 'apertura' | 'clics' | 'ctor' | 'rebote' | 'bajas' | 'envios'

export const METRICAS: Record<Metrica, { label: string; corto: string; pct: boolean; ayuda: string }> = {
  apertura: { label: 'Tasa de apertura', corto: 'Apertura', pct: true, ayuda: 'aperturas / envíos' },
  clics: { label: 'Tasa de clics (CTR)', corto: 'Clics', pct: true, ayuda: 'clics / envíos' },
  ctor: { label: 'Clics sobre aperturas (CTOR)', corto: 'CTOR', pct: true, ayuda: 'clics / aperturas' },
  rebote: { label: 'Tasa de rebote', corto: 'Rebote', pct: true, ayuda: 'rebotes / envíos' },
  bajas: { label: 'Tasa de bajas', corto: 'Bajas', pct: true, ayuda: 'bajas / envíos' },
  envios: { label: 'Correos enviados', corto: 'Enviados', pct: false, ayuda: 'cantidad de correos' },
}

/** Numerador y denominador de cada métrica (para pruebas e intervalos). */
export function fraccion(t: Totales, m: Metrica): { x: number; n: number } {
  switch (m) {
    case 'apertura': return { x: t.vistas, n: t.envios }
    case 'clics': return { x: t.clicks, n: t.envios }
    case 'ctor': return { x: Math.min(t.clicks, t.vistas), n: t.vistas }
    case 'rebote': return { x: t.rebotes, n: t.envios }
    case 'bajas': return { x: t.salidas, n: t.envios }
    case 'envios': return { x: t.envios, n: 1 }
  }
}

/** Valor de la métrica; null si no hay base (no hubo envíos ≠ 0%). */
export function valor(t: Totales, m: Metrica): number | null {
  if (m === 'envios') return t.envios
  const { x, n } = fraccion(t, m)
  return n ? (x / n) * 100 : null
}

export const totalesDe = (c: CampanaMT): Totales => ({
  campanas: 1, envios: c.totalEnvios, vistas: c.totalVistas, clicks: c.totalClicks, rebotes: c.totalRebotes, salidas: c.totalSalidas,
})

export function sumar(cs: CampanaMT[]): Totales {
  const t: Totales = { campanas: 0, envios: 0, vistas: 0, clicks: 0, rebotes: 0, salidas: 0 }
  for (const c of cs) {
    t.campanas++; t.envios += c.totalEnvios; t.vistas += c.totalVistas
    t.clicks += c.totalClicks; t.rebotes += c.totalRebotes; t.salidas += c.totalSalidas
  }
  return t
}

export const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
export const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
export const diasDelMes = (anio: number, mes: number) => new Date(anio, mes + 1, 0).getDate()

// ── Estado compartido ────────────────────────────────────────────────
const todas = ref<CampanaMT[]>([])
const cargando = ref(false)
const error = ref<string | null>(null)
const cargadas = ref(false)
/** Campañas con menos envíos se consideran pruebas y se excluyen (0 = no excluir). */
const minEnvios = ref(30)

async function cargar(forzar = false) {
  if (cargando.value || (cargadas.value && !forzar)) return
  cargando.value = true
  error.value = null
  try {
    todas.value = await getTodasLasCampanas()
    cargadas.value = true
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudieron cargar las campañas.'
  } finally {
    cargando.value = false
  }
}

/** Enviadas con fecha, de la más antigua a la más reciente. */
const enviadas = computed<CampanaFechada[]>(() =>
  todas.value
    .filter(c => c.totalEnvios > 0 && c.fecha)
    .map(c => {
      const f = new Date(c.fecha!.replace(' ', 'T'))
      return { ...c, f, anio: f.getFullYear(), mes: f.getMonth(), dia: f.getDate() }
    })
    .sort((a, b) => a.f.getTime() - b.f.getTime()),
)
const validas = computed(() => enviadas.value.filter(c => c.totalEnvios >= minEnvios.value))
const excluidas = computed(() => enviadas.value.length - validas.value.length)
const anios = computed(() => {
  const s = new Set(validas.value.map(c => c.anio))
  s.add(new Date().getFullYear())
  return [...s].sort((a, b) => b - a)
})

export interface Periodo { anio: number; mes: number | null }
const enPeriodo = (p: Periodo) => validas.value.filter(c => c.anio === p.anio && (p.mes === null || c.mes === p.mes))

export interface PuntoSerie { id: string | number; etiqueta: string; titulo: string; sub?: string; totales: Totales }
export type Granularidad = 'mes' | 'dia' | 'campana'

/** Puntos del eje x para un periodo: los 12 meses, los días del mes o cada campaña. */
function puntos(p: Periodo, por: Granularidad): PuntoSerie[] {
  const cs = enPeriodo(p)
  if (por === 'campana') {
    return cs.map(c => ({
      id: c.id,
      etiqueta: c.f.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' }),
      titulo: c.nombre,
      sub: c.f.toLocaleDateString('es-CO', { dateStyle: 'medium' }),
      totales: totalesDe(c),
    }))
  }
  if (por === 'mes') {
    return MESES.map((m, i) => ({
      id: i,
      etiqueta: MESES_CORTOS[i],
      titulo: `${m[0].toUpperCase()}${m.slice(1)} ${p.anio}`,
      totales: sumar(cs.filter(c => c.mes === i)),
    }))
  }
  const mes = p.mes ?? 0
  return Array.from({ length: diasDelMes(p.anio, mes) }, (_, i) => {
    const d = new Date(p.anio, mes, i + 1)
    return {
      id: i + 1,
      etiqueta: String(i + 1),
      titulo: d.toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' }),
      totales: sumar(cs.filter(c => c.dia === i + 1)),
    }
  })
}

export const nombrePeriodo = (p: Periodo) => (p.mes === null ? String(p.anio) : `${MESES[p.mes]} ${p.anio}`)

export function useEstadisticasCampanas() {
  return { todas, enviadas, validas, excluidas, anios, cargando, error, minEnvios, cargar, enPeriodo, puntos }
}
