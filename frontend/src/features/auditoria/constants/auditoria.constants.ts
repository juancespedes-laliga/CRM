import {
  Heart, UserRound, Users, Building2, Truck, Target, Wrench, Send, UserCog, LayoutGrid,
} from 'lucide-vue-next'
import type {
  AccionAuditoria, ModuloAuditoria, ModuloSeleccion, OrigenAuditoria, VigenciaRenovacion,
} from '../types/auditoria'

export interface ModuloInfo {
  key: ModuloAuditoria
  label: string
  /** Grupo del menú al que pertenece (para agrupar el selector). */
  grupo: 'Plan Liga' | 'Comercial' | 'Marketing' | 'Administración'
  icono: any
  /** Titulares y beneficiarios: tienen fecha de ingreso, renovación y vigencia. */
  planLiga: boolean
  /** Acciones que pueden aparecer en este módulo (para el filtro "Acción"). */
  acciones: AccionAuditoria[]
  /** Texto de la tarjeta en la pantalla de entrada. */
  descripcion: string
  /** Color del ícono y fondo de su recuadro (mismo estilo que el hub de Embudos). */
  color: string
  bg: string
}

const ACCIONES_BASICAS: AccionAuditoria[] = ['creacion', 'edicion', 'activacion', 'desactivacion', 'eliminacion']

export const MODULOS: ModuloInfo[] = [
  {
    key: 'titulares', label: 'Titulares', grupo: 'Plan Liga', icono: Heart, planLiga: true,
    acciones: ['creacion', 'edicion', 'activacion', 'desactivacion', 'renovacion', 'cambio_plan', 'reemplazo', 'eliminacion'],
    descripcion: 'Altas, ediciones, activaciones, renovaciones y cambios de plan de los titulares.',
    color: '#EC4899', bg: '#FCE7F3',
  },
  {
    key: 'beneficiarios', label: 'Beneficiarios', grupo: 'Plan Liga', icono: UserRound, planLiga: true,
    acciones: ['creacion', 'edicion', 'activacion', 'desactivacion', 'renovacion', 'cambio_plan', 'cambio_titular', 'reemplazo', 'eliminacion'],
    descripcion: 'Cambios de los beneficiarios, incluidos reemplazos y traslados de grupo.',
    color: '#8B5CF6', bg: '#EDE9FE',
  },
  {
    key: 'contactos', label: 'Contactos', grupo: 'Comercial', icono: Users, planLiga: false, acciones: ACCIONES_BASICAS,
    descripcion: 'Creación, edición y eliminación de contactos.',
    color: '#2447F9', bg: '#EEF2FF',
  },
  {
    key: 'empresas', label: 'Empresas', grupo: 'Comercial', icono: Building2, planLiga: false, acciones: ACCIONES_BASICAS,
    descripcion: 'Cambios en los datos de las empresas y su estado.',
    color: '#0284C7', bg: '#E0F2FE',
  },
  {
    key: 'proveedores', label: 'Proveedores', grupo: 'Comercial', icono: Truck, planLiga: false, acciones: ACCIONES_BASICAS,
    descripcion: 'Cambios en proveedores y su información de contacto.',
    color: '#059669', bg: '#D1FAE5',
  },
  {
    key: 'oportunidades', label: 'Oportunidades', grupo: 'Comercial', icono: Target, planLiga: false, acciones: ['creacion', 'edicion', 'eliminacion'],
    descripcion: 'Nuevas oportunidades, cambios de etapa y de valor.',
    color: '#EA580C', bg: '#FFEDD5',
  },
  {
    key: 'servicios', label: 'Servicios', grupo: 'Comercial', icono: Wrench, planLiga: false, acciones: ACCIONES_BASICAS,
    descripcion: 'Cambios en el catálogo de servicios, precios y duración.',
    color: '#0D9488', bg: '#CCFBF1',
  },
  {
    key: 'campanas', label: 'Campañas', grupo: 'Marketing', icono: Send, planLiga: false, acciones: ['creacion', 'edicion', 'eliminacion'],
    descripcion: 'Creación y edición de campañas y plantillas de correo.',
    color: '#C9A227', bg: '#FEF9C3',
  },
  {
    key: 'usuarios', label: 'Usuarios', grupo: 'Administración', icono: UserCog, planLiga: false, acciones: ACCIONES_BASICAS,
    descripcion: 'Altas de usuarios del CRM, cambios de rol y desactivaciones.',
    color: '#475569', bg: '#F1F5F9',
  },
]



export const GRUPOS_MODULO = ['Plan Liga', 'Comercial', 'Marketing', 'Administración'] as const

export const MODULO_POR_KEY = Object.fromEntries(MODULOS.map(m => [m.key, m])) as Record<ModuloAuditoria, ModuloInfo>


export const TODAS_LAS_ACCIONES: AccionAuditoria[] = [
  'creacion', 'edicion', 'activacion', 'desactivacion', 'renovacion',
  'cambio_plan', 'cambio_titular', 'reemplazo', 'eliminacion',
]


export const ACCION_LABEL: Record<AccionAuditoria, string> = {
  creacion: 'Creación',
  edicion: 'Edición',
  activacion: 'Activación',
  desactivacion: 'Desactivación',
  renovacion: 'Renovación',
  cambio_plan: 'Cambio de plan',
  cambio_titular: 'Cambio de titular',
  reemplazo: 'Reemplazo',
  eliminacion: 'Eliminación',
}

export const ORIGEN_LABEL: Record<OrigenAuditoria, string> = {
  manual: 'Manual',
  excel: 'Excel',
  grupo: 'Por grupo',
  sistema: 'Sistema',
}

/** Origen masivo: el cambio no se hizo registro por registro. */
export const esOrigenMasivo = (o: OrigenAuditoria) => o === 'excel' || o === 'grupo'

export const VIGENCIA_LABEL: Record<VigenciaRenovacion, string> = {
  vigente: 'Vigente',
  por_vencer: 'Por vencer',
  vencido: 'Vencido',
}

/** Días o menos para considerar una vigencia "por vencer". */
export const DIAS_POR_VENCER = 30

export const POR_PAGINA = 15

// ── Colores ──────────────────────────────────────────────────────────
// Las acciones y orígenes van en gris; el color se reserva para estados:
// verde = activo / renovado, rojo = inactivo / vencido, ámbar = por vencer.

export const CLASE_NEUTRA = 'bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300'

export function claseEstado(estado: string | null | undefined): string {
  switch (estado) {
    case 'Activo': return 'text-emerald-600 dark:text-emerald-400'
    case 'Inactivo':
    case 'Retirado':
    case 'Eliminado': return 'text-red-600 dark:text-red-400'
    default: return 'text-slate-500 dark:text-slate-400'
  }
}

export function claseVigencia(v: VigenciaRenovacion): string {
  switch (v) {
    case 'vigente': return 'text-emerald-600 dark:text-emerald-400'
    case 'por_vencer': return 'text-amber-600 dark:text-amber-400'
    case 'vencido': return 'text-red-600 dark:text-red-400'
  }
}

export const claseRenovado = (r: boolean | null) =>
  r === true ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'

// ── Vistas que se eligen en la pantalla de entrada ──────────────────
// Titulares y beneficiarios se auditan juntos como "Plan Liga"; el resto
// de módulos van cada uno en su tarjeta.

export interface VistaInfo {
  key: ModuloSeleccion
  label: string
  /** Etiqueta pequeña sobre el nombre en la tarjeta. */
  grupo: string
  descripcion: string
  icono: any
  color: string
  bg: string
  /** Módulos que incluye (null = todos). */
  modulos: ModuloAuditoria[] | null
  /** Tiene ingreso / renovación / vigencia y la pestaña Renovaciones. */
  planLiga: boolean
  acciones: AccionAuditoria[]
}

export const VISTAS: VistaInfo[] = [
  {
    key: 'todos', label: 'Todos los módulos', grupo: 'General',
    descripcion: 'El registro completo de lo que se hace en el CRM, más las renovaciones de Plan Liga.',
    icono: LayoutGrid, color: '#4F46E5', bg: '#E0E7FF',
    modulos: null, planLiga: true, acciones: TODAS_LAS_ACCIONES,
  },
  {
    key: 'plan-liga', label: 'Plan Liga', grupo: 'Titulares y beneficiarios',
    descripcion: 'Altas, ediciones, activaciones, renovaciones, reemplazos y cambios de plan o de grupo.',
    icono: Heart, color: '#EC4899', bg: '#FCE7F3',
    modulos: ['titulares', 'beneficiarios'], planLiga: true, acciones: TODAS_LAS_ACCIONES,
  },
  ...MODULOS.filter(m => !m.planLiga).map(m => ({
    key: m.key as ModuloSeleccion, label: m.label, grupo: m.grupo, descripcion: m.descripcion,
    icono: m.icono, color: m.color, bg: m.bg,
    modulos: [m.key], planLiga: false, acciones: m.acciones,
  })),
]

export const VISTA_POR_KEY = Object.fromEntries(VISTAS.map(v => [v.key, v])) as Record<ModuloSeleccion, VistaInfo>

export const esModuloValido = (v: unknown): v is ModuloSeleccion => typeof v === 'string' && v in VISTA_POR_KEY

export const etiquetaModulo = (m: ModuloSeleccion) => VISTA_POR_KEY[m].label

/** La vista incluye datos de Plan Liga (renovación, vigencia, ingreso). */
export const incluyePlanLiga = (m: ModuloSeleccion) => VISTA_POR_KEY[m].planLiga

export const accionesDeModulo = (m: ModuloSeleccion): AccionAuditoria[] => VISTA_POR_KEY[m].acciones

/** Módulos de datos que abarca la vista (todos si es "todos"). */
export const modulosDeVista = (m: ModuloSeleccion): ModuloAuditoria[] => VISTA_POR_KEY[m].modulos ?? MODULOS.map(x => x.key)
