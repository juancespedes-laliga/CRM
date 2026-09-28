export interface Titular {
  id: number
  tipoDocumento: string
  documento: string
  nombre: string
  fechaNacimiento: string
  sexo: 'Masculino' | 'Femenino' | ''
  correo: string
  telefono: string
  direccion: string
  ciudad: string
  departamento: string
  empresa: string
  planContratado: string
  /** Id del plan (tabla intranet_planliga_tipo_plan) al que queda asociado el titular. */
  tipoPlanId: number | null
  tipoPlan: string
  tipoAfiliado: string
  eps: string
  otraEps: string
  planSalud: string
  planNombre: string
  fechaInscripcion: string
  estado: 'Activo' | 'Inactivo'
  /** Número de factura asociado al alta del titular (solo se registra al crear). */
  factura: string
  /** Detalle por plan (nombre + cupo) cuando el titular viene del listado del backend. */
  planesDetalle?: PlanTitular[]
}

export type TitularDraft = Omit<Titular, 'id'>

export interface Beneficiario {
  id: number
  titularId: number
  tipoDocumento: string
  documento: string
  nombre: string
  fechaNacimiento: string
  sexo: 'Masculino' | 'Femenino' | ''
  correo: string
  telefono: string
  direccion: string
  ciudad: string
  departamento: string
  empresa: string
  tipoPlan: string
  eps: string
  otraEps: string
  planSalud: string
  planNombre: string
  estado: 'Activo' | 'Inactivo' | 'Reemplazado' | 'Retirado'
  fechaInscripcion: string
}

export type BeneficiarioDraft = Omit<Beneficiario, 'id' | 'titularId'>

/**
 * Datos de la PERSONA NUEVA para un "reemplazo" (POST .../reemplazar): da de baja al
 * titular/beneficiario actual y da de alta a otra persona en su lugar, heredando
 * plan/cupo/orden. No incluye plan/EPS/cupo/estado porque esos se heredan del anterior.
 */
export type ReemplazoPersonaDraft = {
  tipoDocumento: string
  documento: string
  nombre: string
  fechaNacimiento: string
  sexo: 'Masculino' | 'Femenino' | ''
  correo: string
  telefono: string
  direccion: string
  ciudad: string
  departamento: string
  empresa: string
}

export interface ReemplazoTitularResultado {
  titularAnteriorId: number
  titularNuevo: Titular
  beneficiariosReasignados: number
  usuarioServinteCreado: boolean
  marcadoEnIncle: boolean
  registrosIncleMarcadosAnterior: number
}

export interface ReemplazoBeneficiarioResultado {
  beneficiarioAnteriorId: number
  beneficiarioNuevo: Beneficiario
  usuarioServinteCreado: boolean
  marcadoEnIncle: boolean
  registrosIncleMarcadosAnterior: number
}

export type TipoSeguimiento = 'Llamada' | 'Correo' | 'Reunión' | 'WhatsApp' | 'Mensaje' | 'Nota'

export interface SeguimientoDraft {
  tipo: TipoSeguimiento
  accion: string
  proximoPaso: string
  /** Fecha límite del próximo paso; '' si no se definió una. */
  proximoPasoFecha: string
  fecha: string
  /** Oportunidad a la que queda ligada la actividad en la bitácora; null si el titular aún no tiene una oportunidad asociada. */
  oportunidadId: number | null
}

export type TipoImportacion = 'agregar_grupos' | 'titular' | 'beneficiario'
export type AccionMasiva = 'activar' | 'desactivar'

export interface OpcionImportacion {
  key: TipoImportacion
  label: string
  desc: string
  color: string
  bg: string
}

export interface ResultadoImportacion {
  total: number
  exitosos: number
  errores: number
  detalleErrores: string[]
  /** true cuando la validación de formato encontró errores y no se ejecutó ninguna acción. */
  bloqueado?: boolean
}

export interface ResumenTitularesResponse {
  titulares_activos: number
  beneficiarios_activos: number
}

export interface PlanTitular {
  nombre: string
  activos: number
  cupo: number
}

/** Plan del catálogo (GET /api/titulares-beneficiarios/planes). */
export interface PlanServicio {
  id: number
  nombre: string
  /**
   * Cupo de beneficiarios ya resuelto:
   * - Si BENEFICIARIOS_ADICIONALES tiene valor (>0): 4 (cupo del Plan Estándar) + BENEFICIARIOS_ADICIONALES,
   *   sin importar lo que diga MAX_BENEFICIARIOS (ese campo, en ese caso, no es el cupo real).
   * - Si no: MAX_BENEFICIARIOS tal cual (0 = el plan es solo para el titular, sin beneficiarios).
   */
  cupoBeneficiarios: number
}

export interface PlanCatalogoResponse {
  ID: number
  NOMBRE: string
  TIPO: string | null
  MAX_BENEFICIARIOS: number | null
  BENEFICIARIOS_ADICIONALES: number | null
  DESCRIPCION: string | null
  ESTADO: string | null
}

export interface TitularListadoResponse {
  ID_TITULAR: number
  TITULAR: string
  EMAIL: string | null
  TELEFONO: string | null
  TIPO_DOCUMENTO: string | null
  DOCUMENTO: string
  EMPRESA: string | null
  PLANES: string | null
  BENEFICIARIOS: string | null
  INSCRIPCION: string
  ESTADO: string
}

export interface ListadoTitularesResponse {
  items: TitularListadoResponse[]
  total: number
  limit: number
  offset: number
}

export interface BeneficiarioListadoResponse {
  ID: number
  TIPO_DOCUMENTO: string
  DOCUMENTO: string
  NOMBRE1: string
  NOMBRE2: string | null
  APELLIDO1: string
  APELLIDO2: string | null
  FECHA_NACIMIENTO: string | null
  SEXO: string | null
  DIRECCION: string | null
  CIUDAD: string | null
  DEPARTAMENTO: string | null
  CORREO: string | null
  TELEFONO: string | null
  FECHA_INGRESO: string | null
  EMPRESA: string | null
  TIPO_PLAN: string | null
  EPS: string | null
  OTRAEPS: string | null
  PLAN_SALUD: string | null
  PLAN_NOMBRE: string | null
  ESTADO: string
}

/** Respuesta de POST .../beneficiarios/{id}/cambiar-titular: no trae los campos de plan (EPS, etc.). */
export interface BeneficiarioDetalleResponse {
  ID: number
  TIPO_DOCUMENTO: string | null
  DOCUMENTO: string | null
  NOMBRE1: string | null
  NOMBRE2: string | null
  APELLIDO1: string | null
  APELLIDO2: string | null
  FECHA_NACIMIENTO: string | null
  SEXO: string | null
  DIRECCION: string | null
  CIUDAD: string | null
  DEPARTAMENTO: string | null
  CORREO: string | null
  TELEFONO: string | null
  FECHA_INGRESO: string | null
  EMPRESA: string | null
  TIPO_PLAN: string | null
  ESTADO: string | null
}

export interface TitularDetalleResponse {
  ID_TITULAR: number
  DOCUMENTO: string
  TIPO_DOCUMENTO: string
  NOMBRE1: string
  NOMBRE2: string | null
  APELLIDO1: string
  APELLIDO2: string | null
  FECHA_NACIMIENTO: string | null
  SEXO: string | null
  CORREO: string | null
  TELEFONO: string | null
  DIRECCION: string | null
  CIUDAD: string | null
  DEPARTAMENTO: string | null
  TIPO_PLAN: string | null
  TIPO_PLAN_ID: number | null
  TIPO_AFILIADO: string | null
  EMPRESA: string | null
  EPS: string | null
  OTRAEPS: string | null
  PLAN_SALUD: string | null
  PLAN_NOMBRE: string | null
  ESTADO: string
  FECHA_INGRESO: string | null
}

export interface ReemplazoTitularResultadoResponse {
  titular_anterior_id: number
  titular_nuevo: TitularDetalleResponse
  beneficiarios_reasignados: number
  usuario_servinte_creado: boolean
  marcado_en_incle: boolean
  registros_incle_marcados_anterior: number
}

export interface ReemplazoBeneficiarioResultadoResponse {
  beneficiario_anterior_id: number
  beneficiario_nuevo: BeneficiarioListadoResponse
  usuario_servinte_creado: boolean
  marcado_en_incle: boolean
  registros_incle_marcados_anterior: number
}

