/** Módulos del CRM que registran auditoría. Coincide con la columna MODULO de la tabla de auditoría. */
export type ModuloAuditoria =
  | 'titulares'
  | 'beneficiarios'
  | 'contactos'
  | 'empresas'
  | 'proveedores'
  | 'oportunidades'
  | 'servicios'
  | 'campanas'
  | 'usuarios'

/**
 * Lo que se elige auditar en la pantalla de entrada: todos los módulos,
 * Plan Liga (titulares y beneficiarios juntos) o un módulo puntual.
 */
export type ModuloSeleccion = 'todos' | 'plan-liga' | Exclude<ModuloAuditoria, 'titulares' | 'beneficiarios'>

export type AccionAuditoria =
  | 'creacion'
  | 'edicion'
  | 'activacion'
  | 'desactivacion'
  | 'renovacion'
  | 'cambio_plan'
  | 'cambio_titular'
  | 'reemplazo'
  | 'eliminacion'

/** De dónde salió el cambio: a mano, por carga de Excel, por acción sobre un grupo o un proceso automático. */
export type OrigenAuditoria = 'manual' | 'excel' | 'grupo' | 'sistema'

export interface UsuarioAuditoria {
  id: number
  nombre: string
  usuario: string
  rol: string
}

export interface CampoCambiado {
  /** Nombre técnico del campo (columna). */
  campo: string
  /** Nombre legible para mostrar. */
  etiqueta: string
  antes: string | null
  despues: string | null
}

export interface GrupoTitular {
  id: number
  nombre: string
  documento: string
}

export interface RegistroCambio {
  id: number
  /** Fecha y hora ISO ('AAAA-MM-DDTHH:mm:ss'). */
  fecha: string
  usuario: UsuarioAuditoria
  ip: string
  accion: AccionAuditoria
  origen: OrigenAuditoria
  /** Identificador del lote cuando el cambio vino de una acción masiva (Excel o por grupo). */
  loteId: string | null
  modulo: ModuloAuditoria
  registroId: number
  registroNombre: string
  documento: string
  /** Solo para beneficiarios: el titular del grupo al que pertenece. */
  grupoTitular: GrupoTitular | null
  /** Plan Liga: ID del titular (en beneficiarios, el titular de su grupo). */
  idTitular: number | null
  /** Plan Liga: ID del beneficiario (solo en beneficiarios). */
  idBeneficiario: number | null
  estadoAntes: string | null
  estadoDespues: string | null
  /** Solo Plan Liga (titulares y beneficiarios). Fecha de inscripción: solo en altas nuevas. */
  fechaInscripcion: string | null
  /** Fecha en que se registró la persona en Plan Liga. */
  fechaRegistro: string | null
  fechaIngreso: string | null
  renovado: boolean | null
  fechaRenovado: string | null
  /** Fin de la vigencia en ese momento (ingreso + 1 año). */
  vigenciaHasta: string | null
  motivo: string
  campos: CampoCambiado[]
}

/** Conteo de cambios por módulo, para el selector de módulo. */
export interface ResumenModulo {
  modulo: ModuloAuditoria
  total: number
  ultimoCambio: string | null
}

export type TipoPersonaPlanLiga = 'titular' | 'beneficiario'

export interface RenovacionRegistro {
  tipo: TipoPersonaPlanLiga
  id: number
  nombre: string
  documento: string
  empresa: string
  plan: string
  estado: string
  fechaIngreso: string
  renovado: boolean
  fechaRenovado: string | null
  /** Fecha de vencimiento de la vigencia ('AAAA-MM-DD'). */
  vencimiento: string
  ultimaRenovacionPor: { nombre: string; usuario: string } | null
  /** Solo beneficiarios. */
  titular: { id: number; nombre: string } | null
}

export type VigenciaRenovacion = 'vigente' | 'por_vencer' | 'vencido'

export interface FiltrosCambios {
  buscar: string
  /** Módulo puntual dentro de la vista (p. ej. solo beneficiarios dentro de Plan Liga). */
  submodulo: ModuloAuditoria | 'todos'
  accion: AccionAuditoria | 'todas'
  usuario: number | 'todos'
  origen: OrigenAuditoria | 'todos'
  estado: string
  renovado: 'todos' | 'si' | 'no'
  desde: string
  hasta: string
}

export interface FiltrosRenovaciones {
  buscar: string
  tipo: TipoPersonaPlanLiga | 'todos'
  renovado: 'todos' | 'si' | 'no'
  vigencia: VigenciaRenovacion | 'todas'
  estado: string
}

/** Registro sobre el que se pide el historial (línea de tiempo). */
export interface ObjetivoHistorial {
  modulo: ModuloAuditoria
  registroId: number
  nombre: string
  documento: string
}

export type TabAuditoria = 'cambios' | 'renovaciones'

export interface TarjetaResumen {
  key: string
  label: string
  valor: number
  icono: any
  /** Clase de color del valor (solo para estados; por defecto neutro). */
  claseValor?: string
  ayuda?: string
}
