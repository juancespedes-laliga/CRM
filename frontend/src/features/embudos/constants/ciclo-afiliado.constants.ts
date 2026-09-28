export interface EtapaAfiliado {
  n: string
  color: string
  bg: string
}

// Ciclo de vida: Prospecto → Nuevo → Activo → En riesgo → Por renovar → Renovado / No renovado
export const ETAPAS_AFILIADO: EtapaAfiliado[] = [
  { n: 'Prospecto', color: '#64748B', bg: '#F1F5F9' },
  { n: 'Nuevo', color: '#2447F9', bg: '#EEF2FF' },
  { n: 'Activo', color: '#059669', bg: '#D1FAE5' },
  { n: 'En riesgo', color: '#DC2626', bg: '#FEE2E2' },
  { n: 'Por renovar', color: '#C9A227', bg: '#FEF9C3' },
  { n: 'Renovado', color: '#0F766E', bg: '#CCFBF1' },
  { n: 'No renovado', color: '#EF4444', bg: '#FEE2E2' },
]
export const ETAPA_COLOR: Record<string, string> = Object.fromEntries(ETAPAS_AFILIADO.map(e => [e.n, e.color]))

// ── Opciones de los filtros de segmento ──────────────────────────────
// Nombres como en TMPBI1.MUNICIPIO (el API compara en mayúsculas).
export const CIUDADES = ['PEREIRA', 'DOSQUEBRADAS', 'CARTAGO', 'SANTA ROSA DE CABAL', 'LA VIRGINIA', 'MARSELLA']
export const CONCEPTOS = ['ECOGRAFIA', 'CONSULTA GINECOLOGIA', 'CONSULTA DERMATOLOGICA', 'MEDICAMENTO ONCOLOGICO', 'LABORATORIO']
export const VINCULACIONES = ['Empresa', 'Particular'] as const
export const CANALES_ORIGEN = ['Web', 'Feria de salud', 'Referido', 'Campaña', 'Convenio empresarial']
export const CALLES = [
  'Calle 15 #23-45', 'Carrera 8 #12-34', 'Avenida 30 de Agosto #45-10', 'Calle 21 #9-56',
  'Carrera 6 #18-22', 'Calle 40 #14-08', 'Carrera 4 #7-19', 'Calle 33 #11-27',
]

export const OPC_ULTIMO_USO = [
  { v: '', l: 'Cualquiera' }, { v: 'nunca', l: 'Nunca' },
  { v: '90', l: '+90 días' }, { v: '60', l: '+60 días' }, { v: '30', l: '+30 días' },
]
export const OPC_ANTIGUEDAD = [
  { v: '', l: 'Cualquiera' }, { v: '30', l: '≤ 30 días' }, { v: '90', l: '≤ 90 días' },
  { v: '365', l: '≤ 1 año' }, { v: '+365', l: '+ 1 año' },
]

// Catálogo de servicios (mock). En el CRM real llegaría del backend.
export const SERVICIOS_CATALOGO = [
  'Hemograma IV', 'Creatinina en suero', 'Glucosa en suero', 'Colesterol total',
  'Triglicéridos', 'TSH', 'Perfil lipídico', 'PSA total', 'Uroanálisis',
  'Ecografía abdominal total', 'Ecografía mamaria bilateral', 'Ecografía de tiroides',
  'Consulta medicina general', 'Citología cérvico-uterina', 'Mamografía bilateral',
  'Densitometría ósea', 'Electrocardiograma', 'Prueba de embarazo en sangre',
  'Hemoglobina glicosilada', 'Antígeno prostático',
]
export const SERVICIOS_TOTAL = 184

// ── Afiliados (mock) ────────────────────────────────────────────────
export interface AfiliadoTarjeta {
  id: number
  etapa: string
  nombre: string
  documento: string
  sub: string
  plan: 'Individual' | 'Familiar' | 'Empresarial'
  responsable: string
  dias: number
  nota?: string
  // Campos para los filtros de segmento
  planLiga: boolean
  sexo: 'F' | 'M'
  edad: number
  ciudad: string
  direccion: string
  vinculacion: 'Empresa' | 'Particular'
  origen: string
  conceptos: string[]
  servicios: string[]
  nServicios: number
  ultimoUsoDias: number | null
  antiguedadDias: number
  tieneCorreo: boolean
  tieneCelular: boolean
}

interface AfiliadoBase {
  id: number; etapa: string; nombre: string; sub: string
  plan: AfiliadoTarjeta['plan']; responsable: string; dias: number; nota?: string
}

const BASE: AfiliadoBase[] = [
  { id: 1, etapa: 'Prospecto', nombre: 'Yenifer Tunubalá', sub: 'Pereira · Web', plan: 'Familiar', responsable: 'Diana Ríos', dias: 2 },
  { id: 2, etapa: 'Prospecto', nombre: 'Álvaro Nieto', sub: 'La Virginia · Referido', plan: 'Individual', responsable: 'María García', dias: 6 },
  { id: 3, etapa: 'Prospecto', nombre: 'Familia Quintero', sub: 'Dosquebradas · Feria', plan: 'Familiar', responsable: 'Carlos Torres', dias: 1 },
  { id: 4, etapa: 'Nuevo', nombre: 'Marta Lucía Cardona', sub: 'Inscrita hace 6 días', plan: 'Familiar', responsable: 'Diana Ríos', dias: 6, nota: 'Sin primer uso' },
  { id: 5, etapa: 'Nuevo', nombre: 'Deisy Carolina Muñoz', sub: 'Inscrita hace 12 días', plan: 'Individual', responsable: 'Carlos Torres', dias: 12 },
  { id: 6, etapa: 'Nuevo', nombre: 'Empleados Café y Moda (12)', sub: 'Alta de convenio', plan: 'Empresarial', responsable: 'Carlos Torres', dias: 8, nota: 'Sin primer uso' },
  { id: 7, etapa: 'Activo', nombre: 'Gonzalo Restrepo', sub: '4 servicios en 60 días', plan: 'Individual', responsable: 'Carlos Torres', dias: 45 },
  { id: 8, etapa: 'Activo', nombre: 'Amparo Giraldo', sub: 'Afiliada desde 2019', plan: 'Familiar', responsable: 'Diana Ríos', dias: 210 },
  { id: 9, etapa: 'Activo', nombre: 'Familia Arias Gómez', sub: 'Ecografía usada 09/09', plan: 'Familiar', responsable: 'María García', dias: 32 },
  { id: 10, etapa: 'Activo', nombre: 'Blanca Nieves Aguirre', sub: 'Santa Rosa de Cabal', plan: 'Familiar', responsable: 'Diana Ríos', dias: 120 },
  { id: 11, etapa: 'En riesgo', nombre: 'Héctor Vinasco', sub: '68 días sin uso', plan: 'Individual', responsable: 'Juan López', dias: 68, nota: 'Sin uso' },
  { id: 12, etapa: 'En riesgo', nombre: 'Empleados Audifarma (31)', sub: '74 días sin agenda', plan: 'Empresarial', responsable: 'Diana Ríos', dias: 74, nota: 'Convenio sin uso' },
  { id: 13, etapa: 'En riesgo', nombre: 'Luz Marina Ospina', sub: 'No contesta llamadas', plan: 'Familiar', responsable: 'Juan López', dias: 40 },
  { id: 14, etapa: 'Por renovar', nombre: 'Rosalba Henao', sub: 'Vence 28 sep · T-30', plan: 'Familiar', responsable: 'Diana Ríos', dias: 12 },
  { id: 15, etapa: 'Por renovar', nombre: 'Gustavo Adolfo Marín', sub: 'Vence 12 sep · T-7', plan: 'Individual', responsable: 'Carlos Torres', dias: 20, nota: 'Urgente' },
  { id: 16, etapa: 'Por renovar', nombre: 'Omaira Salazar', sub: 'Vence 10 sep · en gestión', plan: 'Familiar', responsable: 'Juan López', dias: 5 },
  { id: 17, etapa: 'Renovado', nombre: 'Jhon Freddy Loaiza', sub: 'Renovó +1 año · 01/09', plan: 'Individual', responsable: 'María García', dias: 0 },
  { id: 18, etapa: 'Renovado', nombre: 'Nubia Ramírez', sub: 'Renovó +1 año · 29/08', plan: 'Familiar', responsable: 'Diana Ríos', dias: 0 },
  { id: 19, etapa: 'No renovado', nombre: 'Libardo Ospina', sub: 'Motivo: no usó el plan', plan: 'Individual', responsable: 'Juan López', dias: 0, nota: 'Sin uso' },
  { id: 20, etapa: 'No renovado', nombre: 'Cooperativa de Caficultores', sub: 'Motivo: cambió de aliado', plan: 'Empresarial', responsable: 'Carlos Torres', dias: 0 },
]

// Deriva los campos de segmento de forma determinística a partir del id
// (mock estable, sin aleatoriedad entre recargas).
export const AFILIADOS_MOCK: AfiliadoTarjeta[] = BASE.map((a): AfiliadoTarjeta => {
  const s = a.id
  const servicios = SERVICIOS_CATALOGO.filter((_, i) => (s + i) % 4 === 0).slice(0, 5)
  const sinUso = a.nota?.toLowerCase().includes('sin uso') || a.nota?.toLowerCase().includes('sin primer uso') || a.etapa === 'Prospecto'
  return {
    ...a,
    documento: String(24000000 + s * 9137643),
    planLiga: a.etapa !== 'Prospecto',
    sexo: s % 3 === 0 ? 'M' : 'F',
    edad: 21 + (s * 13) % 58,
    ciudad: CIUDADES[s % CIUDADES.length],
    direccion: `${CALLES[s % CALLES.length]}, ${CIUDADES[s % CIUDADES.length]}`,
    vinculacion: a.plan === 'Empresarial' ? 'Empresa' : 'Particular',
    origen: a.plan === 'Empresarial' ? 'Convenio empresarial' : CANALES_ORIGEN[s % 4],
    conceptos: CONCEPTOS.filter((_, i) => ((s >> i) & 1) === 1),
    servicios,
    nServicios: sinUso ? 0 : servicios.length,
    ultimoUsoDias: sinUso ? null : 4 + (s * 17) % 300,
    antiguedadDias: a.etapa === 'Prospecto' ? 0 : 15 + (s * 61) % 900,
    tieneCorreo: s % 4 !== 0,
    tieneCelular: s % 6 !== 0,
  }
})

export const RESPONSABLES = [...new Set(AFILIADOS_MOCK.map(a => a.responsable))].sort()

// ── Filtro de segmento (compartido por el segmentador y los segmentos) ──
export interface FiltroSegmento {
  planLiga: '' | 'Plan Liga' | 'No plan Liga'
  // Solo aplica junto con planLiga === 'Plan Liga' (ver FiltrosSegmento.vue):
  // sale de INTRANET_PLANLIGA/INTRANET_PLANLIGA_BENEFICIARIO, no de TMPBI1.
  usoPlan: '' | 'con_uso' | 'sin_uso'
  sexo: '' | 'F' | 'M'
  edadMin: string
  edadMax: string
  departamento: string
  ciudades: string[]
  etapas: string[]
  origen: string
  responsable: string
  conceptos: string[]
  servicios: string[]
  ultimoUso: string
  antiguedad: string
  vinculacion: string
  conCorreo: boolean
  conCelular: boolean
}

export const filtroVacio = (): FiltroSegmento => ({
  planLiga: '', usoPlan: '', sexo: '', edadMin: '', edadMax: '',
  departamento: '', ciudades: [], etapas: [], origen: '', responsable: '',
  conceptos: [], servicios: [],
  ultimoUso: '', antiguedad: '', vinculacion: '',
  conCorreo: false, conCelular: false,
})

export const clonarFiltro = (f: FiltroSegmento): FiltroSegmento => JSON.parse(JSON.stringify(f))

export const contarFiltros = (f: FiltroSegmento): number =>
  (f.planLiga ? 1 : 0) + (f.usoPlan ? 1 : 0) + (f.sexo ? 1 : 0) + (f.edadMin || f.edadMax ? 1 : 0)
  + (f.departamento ? 1 : 0) + f.ciudades.length + f.etapas.length + (f.origen ? 1 : 0) + (f.responsable ? 1 : 0)
  + f.conceptos.length + f.servicios.length
  + (f.ultimoUso ? 1 : 0) + (f.antiguedad ? 1 : 0)
  + (f.vinculacion ? 1 : 0) + (f.conCorreo ? 1 : 0) + (f.conCelular ? 1 : 0)

// Convierte un filtro en etiquetas legibles (para mostrar como "criterios").
export function resumirFiltros(f: FiltroSegmento): string[] {
  const c: string[] = []
  if (f.planLiga) c.push(f.planLiga)
  if (f.usoPlan) c.push(f.usoPlan === 'con_uso' ? 'Con uso del plan' : 'Sin uso del plan')
  if (f.sexo) c.push(f.sexo === 'F' ? 'Mujeres' : 'Hombres')
  if (f.edadMin || f.edadMax) c.push(`Edad ${f.edadMin || '0'}–${f.edadMax || '∞'}`)
  if (f.departamento) c.push(`Departamento: ${f.departamento}`)
  if (f.ciudades.length) c.push(`Ciudad: ${f.ciudades.join(', ')}`)
  if (f.etapas.length) c.push(`Etapa: ${f.etapas.join(', ')}`)
  if (f.origen) c.push(`Origen: ${f.origen}`)
  if (f.responsable) c.push(`Responsable: ${f.responsable}`)
  if (f.conceptos.length) c.push(`Concepto: ${f.conceptos.join(', ')}`)
  if (f.servicios.length) c.push(`Servicio: ${f.servicios.join(', ')}`)
  if (f.ultimoUso) c.push(`Último uso: ${f.ultimoUso === 'nunca' ? 'Nunca' : '+' + f.ultimoUso + ' días'}`)
  if (f.antiguedad) c.push(`Antigüedad: ${f.antiguedad.startsWith('+') ? '+ 1 año' : '≤ ' + f.antiguedad + ' días'}`)
  if (f.vinculacion) c.push(`Vinculación: ${f.vinculacion}`)
  if (f.conCorreo) c.push('Solo con correo')
  if (f.conCelular) c.push('Solo con celular')
  return c
}

export function afiliadoCoincide(x: AfiliadoTarjeta, f: FiltroSegmento): boolean {
  if (f.planLiga === 'Plan Liga' && !x.planLiga) return false
  if (f.planLiga === 'No plan Liga' && x.planLiga) return false
  if (f.sexo && x.sexo !== f.sexo) return false
  if (f.edadMin && x.edad < +f.edadMin) return false
  if (f.edadMax && x.edad > +f.edadMax) return false
  if (f.ciudades.length && !f.ciudades.includes(x.ciudad)) return false
  if (f.etapas.length && !f.etapas.includes(x.etapa)) return false
  if (f.origen && x.origen !== f.origen) return false
  if (f.responsable && x.responsable !== f.responsable) return false
  if (f.conceptos.length && !f.conceptos.some(c => x.conceptos.includes(c))) return false
  if (f.servicios.length && !f.servicios.some(s => x.servicios.includes(s))) return false
  if (f.ultimoUso) {
    const d = x.ultimoUsoDias
    if (f.ultimoUso === 'nunca' && d !== null) return false
    if (f.ultimoUso === '90' && !(d === null || d > 90)) return false
    if (f.ultimoUso === '60' && !(d === null || d > 60)) return false
    if (f.ultimoUso === '30' && !(d === null || d > 30)) return false
  }
  if (f.antiguedad === '30' && x.antiguedadDias > 30) return false
  if (f.antiguedad === '90' && x.antiguedadDias > 90) return false
  if (f.antiguedad === '365' && x.antiguedadDias > 365) return false
  if (f.antiguedad === '+365' && x.antiguedadDias <= 365) return false
  if (f.vinculacion && x.vinculacion !== f.vinculacion) return false
  if (f.conCorreo && !x.tieneCorreo) return false
  if (f.conCelular && !x.tieneCelular) return false
  return true
}

// ── Plantillas (mock) para el envío desde el segmento ────────────────
export interface PlantillaRef {
  id: string
  nombre: string
  resumen: string
}
export const PLANTILLAS_CORREO: PlantillaRef[] = [
  { id: 'c-bienvenida', nombre: 'Bienvenida — nuevo afiliado', resumen: 'Asunto: ¡Bienvenido(a) a la Fundación La Liga Ama Salvar Vidas!' },
  { id: 'c-reactivacion', nombre: 'Reactivación — sin uso', resumen: 'Recuerda tus chequeos preventivos sin costo adicional.' },
  { id: 'c-renovacion', nombre: 'Recordatorio de renovación', resumen: 'Tu Plan Liga está por vencer, renueva a tiempo.' },
  { id: 'c-tamizaje', nombre: 'Campaña de tamizaje', resumen: 'Agenda tu mamografía / citología del año.' },
]
export const PLANTILLAS_WHATSAPP: PlantillaRef[] = [
  { id: 'w-bienvenida', nombre: 'Bienvenida', resumen: 'Hola {nombre} 👋 Ya eres parte del Plan Liga…' },
  { id: 'w-agenda', nombre: 'Invitación a agendar', resumen: 'Agenda tu chequeo preventivo aquí 👉 {link}' },
  { id: 'w-renovacion', nombre: 'Renovación T-7', resumen: 'Tu Plan Liga vence el {fecha}. Responde SÍ y te ayudamos.' },
  { id: 'w-encuesta', nombre: 'Encuesta de satisfacción', resumen: '¿Cómo te fue en tu última cita? Cuéntanos del 1 al 5.' },
]
