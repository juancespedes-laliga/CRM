import type {
  Beneficiario, BeneficiarioDraft, Titular, TitularDraft,
  ResumenTitularesResponse, TitularListadoResponse, ListadoTitularesResponse,
  BeneficiarioListadoResponse, BeneficiarioDetalleResponse, TitularDetalleResponse, PlanTitular, PlanServicio, PlanCatalogoResponse,
  ReemplazoPersonaDraft, ReemplazoTitularResultado, ReemplazoBeneficiarioResultado,
  ReemplazoTitularResultadoResponse, ReemplazoBeneficiarioResultadoResponse,
  SeguimientoDraft, TipoSeguimiento,
} from '../types/plan-liga'
import { joinNombreCompleto, splitNombreCompleto } from '@/shared/utils/nombreCompuesto'
import { authHeader } from '@/features/auth/composables/useAuth'

const API_URL = import.meta.env.VITE_CRM_API_URL

async function obtenerJson<T>(ruta: string, mensajeError: string): Promise<T> {
  const response = await fetch(`${API_URL}${ruta}`, { headers: authHeader() })
  if (!response.ok) await lanzarErrorConDetalle(response, mensajeError)
  return response.json()
}

// El backend devuelve el motivo puntual del rechazo en { detail }
// (ej. "el titular {id} está inactivo"); se usa ese mensaje en vez de uno genérico.
async function lanzarErrorConDetalle(response: Response, mensajeError: string): Promise<never> {
  const body = await response.json().catch(() => null)
  const detail = typeof body?.detail === 'string' ? body.detail : null
  throw new Error(detail ?? mensajeError)
}

// Quita comas, puntos, guiones, numerales y demás caracteres raros de la dirección
// antes de mandarla al backend (deja solo letras, números y espacios).
function limpiarDireccion(direccion: string): string {
  return direccion
    .replace(/[^\p{L}\p{N}\s]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
}

// El backend no es consistente con el formato de fecha que devuelve en lectura: unas veces
// 'DD/MM/AAAA' (ej. FECHA_INGRESO, y FECHA_NACIMIENTO de titular) y otras 'AAAA-MM-DD' (ej.
// FECHA_NACIMIENTO de beneficiario). El resto de la app (drafts, FechaInput) siempre trabaja
// en 'AAAA-MM-DD'; sin esta normalización, el datepicker de edición recibe un string que no
// puede parsear y muestra "NaN/NaN/NaN".
function fechaApiAIso(fecha: string | null): string {
  if (!fecha) return ''
  const ddmmaaaa = fecha.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (ddmmaaaa) {
    const [, dia, mes, anio] = ddmmaaaa
    return `${anio}-${mes}-${dia}`
  }
  const iso = fecha.match(/^(\d{4}-\d{2}-\d{2})/)
  return iso ? iso[1] : fecha
}

const ESTADO_TITULAR_API: Record<Titular['estado'], string> = { Activo: 'A', Inactivo: 'I' }
const SEXO_TITULAR_API: Record<Titular['sexo'], string | null> = { Masculino: 'M', Femenino: 'F', '': null }

// enviarCorreoRegistro en false solo desde la carga masiva por Excel (cargaMasiva.ts):
// un alta manual individual si manda el correo, una importacion de muchos no.
export async function createTitular(data: TitularDraft, enviarCorreoRegistro = true): Promise<void> {
  const { nombre1, nombre2, apellido1, apellido2 } = splitNombreCompleto(data.nombre)
  const body = {
    TIPO_PLAN: data.tipoPlan,
    TIPO_DOCUMENTO: data.tipoDocumento,
    DOCUMENTO: data.documento,
    NOMBRE1: nombre1,
    NOMBRE2: nombre2,
    APELLIDO1: apellido1,
    APELLIDO2: apellido2,
    FECHA_NACIMIENTO: data.fechaNacimiento,
    SEXO: SEXO_TITULAR_API[data.sexo],
    DIRECCION: limpiarDireccion(data.direccion),
    CIUDAD: data.ciudad,
    DEPARTAMENTO: data.departamento,
    CORREO: data.correo,
    TELEFONO: data.telefono,
    FECHA_INGRESO: data.fechaInscripcion,
    TIPO_AFILIADO: data.tipoAfiliado,
    EMPRESA: data.empresa,
    EPS: data.eps,
    OTRAEPS: data.otraEps,
    PLAN_SALUD: data.planSalud,
    PLAN_NOMBRE: data.planNombre,
    // null es el Plan Estándar (cupo 4): se manda tal cual, no se convierte a 0.
    TIPO_PLAN_ID: data.tipoPlanId,
    FACTURA: data.factura || null,
    ENVIAR_CORREO_REGISTRO: enviarCorreoRegistro,
  }
  // El backend resuelve el usuario creador (USUARIO_ID en INTRANET_PREPLANLIGA) a partir
  // del Bearer token, igual que /api/bitacora/: sin este header, get_current_username falla.
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo crear el titular.')
}

export async function updateTitular(id: number, data: TitularDraft): Promise<Titular> {
  const { nombre1, nombre2, apellido1, apellido2 } = splitNombreCompleto(data.nombre)
  const body = {
    DOCUMENTO: data.documento,
    TIPO_DOCUMENTO: data.tipoDocumento,
    NOMBRE1: nombre1,
    NOMBRE2: nombre2,
    APELLIDO1: apellido1,
    APELLIDO2: apellido2,
    FECHA_NACIMIENTO: data.fechaNacimiento,
    SEXO: SEXO_TITULAR_API[data.sexo],
    CORREO: data.correo,
    TELEFONO: data.telefono,
    DIRECCION: limpiarDireccion(data.direccion),
    CIUDAD: data.ciudad,
    DEPARTAMENTO: data.departamento,
    EMPRESA: data.empresa,
    ESTADO: ESTADO_TITULAR_API[data.estado],
  }
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo actualizar el titular.')
  return { ...data, id }
}

export async function activarTitular(
  idTitular: number,
  fechaIngreso: string,
  aplicarAGrupo = true,
  // Cambio de plan al renovar (opcional): cambiarPlan es el toggle explícito, ver
  // CAMBIAR_PLAN en schemas.py. tipoPlanId null es "Plan Estándar", una elección válida.
  cambiarPlan = false,
  tipoPlan?: string | null,
  tipoPlanId?: number | null,
): Promise<void> {
  const body: Record<string, unknown> = {
    FECHA_INGRESO: fechaIngreso,
    APLICAR_A_GRUPO: aplicarAGrupo,
    CAMBIAR_PLAN: cambiarPlan,
  }
  if (cambiarPlan) {
    body.TIPO_PLAN = tipoPlan ?? null
    body.TIPO_PLAN_ID = tipoPlanId ?? null
  }
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/activar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo activar el titular.')
}

export interface CambioFechaIngresoGrupoResultado {
  titularesActualizados: number
  beneficiariosActualizados: number
}

// El grupo se define por empresa O por tipo de plan (exactamente uno de los
// dos -- el backend rechaza si vienen ambos o ninguno).
export interface GrupoRef {
  empresa?: string
  tipoPlan?: string
}

// Cuenta cuantos titulares/beneficiarios activos del grupo se verian
// afectados, sin modificar nada: para el mensaje de confirmacion antes de aplicar.
export async function contarGrupoActivo(grupo: GrupoRef): Promise<CambioFechaIngresoGrupoResultado> {
  const params = new URLSearchParams()
  if (grupo.empresa) params.set('empresa', grupo.empresa)
  if (grupo.tipoPlan) params.set('tipo_plan', grupo.tipoPlan)
  const response = await fetch(
    `${API_URL}/api/titulares-beneficiarios/grupo/conteo?${params}`,
    { headers: authHeader() },
  )
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo calcular cuántos registros se verían afectados.')
  const r = await response.json()
  return { titularesActualizados: r.titulares_actualizados, beneficiariosActualizados: r.beneficiarios_actualizados }
}

// Tipos de plan distintos (INTRANET_PLANLIGA.TIPO_PLAN), para poder elegir un
// grupo por tipo de plan en vez de por empresa.
export async function getTiposPlan(): Promise<string[]> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/grupo/tipos-plan`, { headers: authHeader() })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo cargar la lista de tipos de plan.')
  const data = await response.json() as { valores: string[] }
  return data.valores
}

// Cambia FECHA_INGRESO a todos los titulares activos del grupo (empresa o
// tipo de plan) y a los beneficiarios activos de esos titulares, de una sola vez.
export async function cambiarFechaIngresoGrupo(
  grupo: GrupoRef,
  fechaIngreso: string,
): Promise<CambioFechaIngresoGrupoResultado> {
  const body: Record<string, unknown> = { FECHA_INGRESO: fechaIngreso }
  if (grupo.empresa) body.EMPRESA = grupo.empresa
  if (grupo.tipoPlan) body.TIPO_PLAN = grupo.tipoPlan
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/grupo/fecha-ingreso`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo cambiar la fecha de ingreso del grupo.')
  const r = await response.json()
  return { titularesActualizados: r.titulares_actualizados, beneficiariosActualizados: r.beneficiarios_actualizados }
}

export async function desactivarTitular(idTitular: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/desactivar`, {
    method: 'POST',
    headers: { ...authHeader() },
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo desactivar el titular.')
}

// Cuerpo del POST .../reemplazar: datos de la PERSONA NUEVA (sin plan/EPS/cupo, se heredan
// del titular/beneficiario anterior). Compartido entre reemplazarTitular y reemplazarBeneficiario.
const SEXO_REEMPLAZO_API: Record<ReemplazoPersonaDraft['sexo'], string | null> = { Masculino: 'M', Femenino: 'F', '': null }

function construirBodyReemplazoPersona(data: ReemplazoPersonaDraft) {
  const { nombre1, nombre2, apellido1, apellido2 } = splitNombreCompleto(data.nombre)
  return {
    TIPO_DOCUMENTO: data.tipoDocumento,
    DOCUMENTO: data.documento,
    NOMBRE1: nombre1,
    NOMBRE2: nombre2,
    APELLIDO1: apellido1,
    APELLIDO2: apellido2,
    FECHA_NACIMIENTO: data.fechaNacimiento || null,
    SEXO: SEXO_REEMPLAZO_API[data.sexo],
    DIRECCION: limpiarDireccion(data.direccion),
    CIUDAD: data.ciudad,
    DEPARTAMENTO: data.departamento,
    CORREO: data.correo,
    TELEFONO: data.telefono,
    EMPRESA: data.empresa,
  }
}

// Da de baja al titular actual y da de alta a una PERSONA NUEVA en su lugar, heredando
// plan/cupo/orden e incluyendo altas/bajas en Servinte (ABPAC/INCLE). Distinto de updateTitular:
// no es una corrección de datos in-place, es un reemplazo de persona con más consecuencias.
export async function reemplazarTitular(idTitular: number, data: ReemplazoPersonaDraft): Promise<ReemplazoTitularResultado> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/reemplazar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(construirBodyReemplazoPersona(data)),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo reemplazar el titular.')
  const r: ReemplazoTitularResultadoResponse = await response.json()
  return {
    titularAnteriorId: r.titular_anterior_id,
    titularNuevo: mapTitularDetalle(r.titular_nuevo),
    beneficiariosReasignados: r.beneficiarios_reasignados,
    usuarioServinteCreado: r.usuario_servinte_creado,
    marcadoEnIncle: r.marcado_en_incle,
    registrosIncleMarcadosAnterior: r.registros_incle_marcados_anterior,
  }
}

const ESTADO_BENEFICIARIO_API: Record<Beneficiario['estado'], string> = {
  Activo: 'A', Inactivo: 'I', Reemplazado: 'R', Retirado: 'X',
}
const SEXO_BENEFICIARIO_API: Record<Beneficiario['sexo'], string | null> = { Masculino: 'M', Femenino: 'F', '': null }

// enviarCorreoBienvenida en false solo desde la carga masiva por Excel (cargaMasiva.ts):
// un alta manual individual si manda el correo, una importacion de muchos no.
export async function createBeneficiario(idTitular: number, data: BeneficiarioDraft, enviarCorreoBienvenida = true): Promise<void> {
  const { nombre1, nombre2, apellido1, apellido2 } = splitNombreCompleto(data.nombre)
  const body = {
    TIPO_DOCUMENTO: data.tipoDocumento,
    DOCUMENTO: data.documento,
    NOMBRE1: nombre1,
    NOMBRE2: nombre2,
    APELLIDO1: apellido1,
    APELLIDO2: apellido2,
    FECHA_NACIMIENTO: data.fechaNacimiento,
    SEXO: SEXO_BENEFICIARIO_API[data.sexo],
    DIRECCION: limpiarDireccion(data.direccion),
    CIUDAD: data.ciudad,
    DEPARTAMENTO: data.departamento,
    CORREO: data.correo,
    TELEFONO: data.telefono,
    EMPRESA: data.empresa,
    EPS: data.eps,
    OTRAEPS: data.otraEps,
    PLAN_SALUD: data.planSalud,
    PLAN_NOMBRE: data.planNombre,
    // FECHA_INGRESO no se manda: el backend la hereda automáticamente de la del titular.
    ENVIAR_CORREO_BIENVENIDA: enviarCorreoBienvenida,
  }
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/beneficiarios`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo crear el beneficiario.')
}

export async function updateBeneficiario(idTitular: number, idBeneficiario: number, data: BeneficiarioDraft): Promise<Beneficiario> {
  const { nombre1, nombre2, apellido1, apellido2 } = splitNombreCompleto(data.nombre)
  const body = {
    TIPO_DOCUMENTO: data.tipoDocumento,
    DOCUMENTO: data.documento,
    NOMBRE1: nombre1,
    NOMBRE2: nombre2,
    APELLIDO1: apellido1,
    APELLIDO2: apellido2,
    FECHA_NACIMIENTO: data.fechaNacimiento,
    SEXO: SEXO_BENEFICIARIO_API[data.sexo],
    DIRECCION: limpiarDireccion(data.direccion),
    CIUDAD: data.ciudad,
    DEPARTAMENTO: data.departamento,
    CORREO: data.correo,
    TELEFONO: data.telefono,
    EMPRESA: data.empresa,
    TIPO_PLAN: data.tipoPlan,
    EPS: data.eps,
    OTRAEPS: data.otraEps,
    PLAN_SALUD: data.planSalud,
    PLAN_NOMBRE: data.planNombre,
    ESTADO: ESTADO_BENEFICIARIO_API[data.estado],
  }
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/beneficiarios/${idBeneficiario}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo actualizar el beneficiario.')
  return { ...data, id: idBeneficiario, titularId: idTitular }
}

export async function getResumenTitulares(): Promise<ResumenTitularesResponse> {
  return obtenerJson<ResumenTitularesResponse>(
    '/api/titulares-beneficiarios/resumen',
    'No se pudo cargar el resumen de titulares.',
  )
}

const ESTADO_API: Record<'Activo' | 'Inactivo', string> = { Activo: 'activo', Inactivo: 'inactivo' }
const SEXO_API: Record<'Masculino' | 'Femenino', string> = { Masculino: 'M', Femenino: 'F' }

export interface FiltrosTitulares {
  estado?: 'Activo' | 'Inactivo'
  /** null filtra el bucket "Plan Estándar" (tipo_plan_id IS NULL en el backend). */
  tipoPlanId?: number | null
  sexo?: 'Masculino' | 'Femenino'
  edad?: '0-17' | '18-35' | '36-50' | '51+'
  busqueda?: string
}

export interface ListadoTitularesParams extends FiltrosTitulares {
  limit?: number
  offset?: number
}

// Compartido entre /listado y /exportar: arman los mismos query params de filtro.
function construirQueryFiltrosTitulares(params: FiltrosTitulares): URLSearchParams {
  const query = new URLSearchParams()
  if (params.estado) query.set('estado', ESTADO_API[params.estado])
  if (params.tipoPlanId !== undefined) query.set('tipo_plan_id', params.tipoPlanId === null ? 'null' : String(params.tipoPlanId))
  if (params.sexo) query.set('sexo', SEXO_API[params.sexo])
  if (params.edad) query.set('edad', params.edad)
  if (params.busqueda) query.set('busqueda', params.busqueda)
  return query
}

export interface ListadoTitulares {
  items: Titular[]
  total: number
  limit: number
  offset: number
}

// El backend puede traer BENEFICIARIOS (conteo real) sin PLANES (nombre) cuando el
// titular no tiene un plan vinculado correctamente; no se descartan esos conteos solo
// porque falte el nombre del plan.
function parsePlanesDetalle(planesStr: string | null, beneficiariosStr: string | null): PlanTitular[] {
  const nombres = (planesStr ?? '').split('|').map(s => s.trim()).filter(Boolean)
  const cupos = (beneficiariosStr ?? '').split('|').map(s => s.trim()).filter(Boolean)
  const cantidad = Math.max(nombres.length, cupos.length)
  return Array.from({ length: cantidad }, (_, i) => {
    const [activos, cupo] = (cupos[i] ?? '0/0').split('/').map(n => Number(n) || 0)
    return { nombre: nombres[i] ?? '', activos, cupo }
  })
}

function mapTitularListado(r: TitularListadoResponse): Titular {
  const planesDetalle = parsePlanesDetalle(r.PLANES, r.BENEFICIARIOS)
  return {
    id: r.ID_TITULAR,
    tipoDocumento: r.TIPO_DOCUMENTO ?? '',
    documento: r.DOCUMENTO,
    nombre: r.TITULAR,
    fechaNacimiento: '',
    sexo: '',
    correo: r.EMAIL ?? '',
    telefono: r.TELEFONO ?? '',
    direccion: '',
    ciudad: '',
    departamento: '',
    empresa: r.EMPRESA ?? '',
    planContratado: planesDetalle.map(p => p.nombre).join(' | '),
    tipoPlanId: null,
    tipoPlan: r.TIPO_PLAN ?? '',
    tipoAfiliado: '',
    eps: '',
    otraEps: '',
    planSalud: '',
    planNombre: '',
    fechaInscripcion: r.INSCRIPCION,
    estado: r.ESTADO === 'A' ? 'Activo' : 'Inactivo',
    factura: '',
    planesDetalle,
  }
}

const SEXO_DESDE_API: Record<string, 'Masculino' | 'Femenino' | undefined> = { M: 'Masculino', F: 'Femenino' }

function mapTitularDetalle(r: TitularDetalleResponse): Titular {
  return {
    id: r.ID_TITULAR,
    tipoDocumento: r.TIPO_DOCUMENTO ?? '',
    documento: r.DOCUMENTO,
    nombre: joinNombreCompleto({
      nombre1: r.NOMBRE1 ?? '',
      nombre2: r.NOMBRE2 ?? '',
      apellido1: r.APELLIDO1 ?? '',
      apellido2: r.APELLIDO2 ?? '',
    }),
    fechaNacimiento: fechaApiAIso(r.FECHA_NACIMIENTO),
    sexo: (r.SEXO && SEXO_DESDE_API[r.SEXO]) || '',
    correo: r.CORREO ?? '',
    telefono: r.TELEFONO ?? '',
    direccion: r.DIRECCION ?? '',
    ciudad: r.CIUDAD ?? '',
    departamento: r.DEPARTAMENTO ?? '',
    empresa: r.EMPRESA ?? '',
    planContratado: '',
    tipoPlanId: r.TIPO_PLAN_ID,
    tipoPlan: r.TIPO_PLAN ?? '',
    tipoAfiliado: r.TIPO_AFILIADO ?? '',
    eps: r.EPS ?? '',
    otraEps: r.OTRAEPS ?? '',
    planSalud: r.PLAN_SALUD ?? '',
    planNombre: r.PLAN_NOMBRE ?? '',
    fechaInscripcion: fechaApiAIso(r.FECHA_INGRESO),
    estado: r.ESTADO === 'A' ? 'Activo' : 'Inactivo',
    factura: '',
  }
}

function mapBeneficiarioListado(r: BeneficiarioListadoResponse, titularId: number): Beneficiario {
  return {
    id: r.ID,
    titularId,
    tipoDocumento: r.TIPO_DOCUMENTO ?? '',
    documento: r.DOCUMENTO,
    nombre: joinNombreCompleto({
      nombre1: r.NOMBRE1 ?? '',
      nombre2: r.NOMBRE2 ?? '',
      apellido1: r.APELLIDO1 ?? '',
      apellido2: r.APELLIDO2 ?? '',
    }),
    fechaNacimiento: fechaApiAIso(r.FECHA_NACIMIENTO),
    sexo: (r.SEXO && SEXO_DESDE_API[r.SEXO]) || '',
    correo: r.CORREO ?? '',
    telefono: r.TELEFONO ?? '',
    direccion: r.DIRECCION ?? '',
    ciudad: r.CIUDAD ?? '',
    departamento: r.DEPARTAMENTO ?? '',
    empresa: r.EMPRESA ?? '',
    tipoPlan: r.TIPO_PLAN ?? '',
    eps: r.EPS ?? '',
    otraEps: r.OTRAEPS ?? '',
    planSalud: r.PLAN_SALUD ?? '',
    planNombre: r.PLAN_NOMBRE ?? '',
    estado: r.ESTADO === 'A' ? 'Activo' : 'Inactivo',
    fechaInscripcion: fechaApiAIso(r.FECHA_INGRESO),
  }
}

export async function getBeneficiariosTitular(
  idTitular: number,
  estado: 'A' | 'I' = 'A',
): Promise<Beneficiario[]> {
  const data = await obtenerJson<BeneficiarioListadoResponse[]>(
    `/api/titulares-beneficiarios/${idTitular}/beneficiarios?estado=${estado}`,
    'No se pudo cargar los beneficiarios del titular.',
  )
  return data.map(r => mapBeneficiarioListado(r, idTitular))
}

export async function activarBeneficiario(idTitular: number, idBeneficiario: number, fechaIngreso: string): Promise<Beneficiario> {
  const body = { FECHA_INGRESO: fechaIngreso }
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/beneficiarios/${idBeneficiario}/activar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo activar el beneficiario.')
  const data: { beneficiario: BeneficiarioListadoResponse } = await response.json()
  return mapBeneficiarioListado(data.beneficiario, idTitular)
}

export async function desactivarBeneficiario(idTitular: number, idBeneficiario: number): Promise<Beneficiario> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/beneficiarios/${idBeneficiario}/desactivar`, {
    method: 'POST',
    headers: { ...authHeader() },
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo desactivar el beneficiario.')
  const data: { beneficiario: BeneficiarioListadoResponse } = await response.json()
  return mapBeneficiarioListado(data.beneficiario, idTitular)
}

// Variante usada por la acción masiva (Excel): identifica al beneficiario por su propio
// documento, sin necesidad de conocer ni buscar a su titular.
export async function activarBeneficiarioPorDocumento(documento: string, fechaIngreso: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/beneficiarios/${documento}/activar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify({ FECHA_INGRESO: fechaIngreso }),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo activar el beneficiario.')
}

export async function desactivarBeneficiarioPorDocumento(documento: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/beneficiarios/${documento}/desactivar`, {
    method: 'POST',
    headers: { ...authHeader() },
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo desactivar el beneficiario.')
}

// Da de baja al beneficiario actual y da de alta a una PERSONA NUEVA en su lugar, heredando
// plan/cupo/orden e incluyendo altas/bajas en Servinte (ABPAC/INCLE). Distinto de updateBeneficiario:
// no es una corrección de datos in-place, es un reemplazo de persona con más consecuencias.
export async function reemplazarBeneficiario(idTitular: number, idBeneficiario: number, data: ReemplazoPersonaDraft): Promise<ReemplazoBeneficiarioResultado> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/beneficiarios/${idBeneficiario}/reemplazar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(construirBodyReemplazoPersona(data)),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo reemplazar el beneficiario.')
  const r: ReemplazoBeneficiarioResultadoResponse = await response.json()
  return {
    beneficiarioAnteriorId: r.beneficiario_anterior_id,
    beneficiarioNuevo: mapBeneficiarioListado(r.beneficiario_nuevo, idTitular),
    usuarioServinteCreado: r.usuario_servinte_creado,
    marcadoEnIncle: r.marcado_en_incle,
    registrosIncleMarcadosAnterior: r.registros_incle_marcados_anterior,
  }
}

function mapBeneficiarioDetalle(r: BeneficiarioDetalleResponse, titularId: number): Beneficiario {
  return {
    id: r.ID,
    titularId,
    tipoDocumento: r.TIPO_DOCUMENTO ?? '',
    documento: r.DOCUMENTO ?? '',
    nombre: joinNombreCompleto({
      nombre1: r.NOMBRE1 ?? '',
      nombre2: r.NOMBRE2 ?? '',
      apellido1: r.APELLIDO1 ?? '',
      apellido2: r.APELLIDO2 ?? '',
    }),
    fechaNacimiento: fechaApiAIso(r.FECHA_NACIMIENTO),
    sexo: (r.SEXO && SEXO_DESDE_API[r.SEXO]) || '',
    correo: r.CORREO ?? '',
    telefono: r.TELEFONO ?? '',
    direccion: r.DIRECCION ?? '',
    ciudad: r.CIUDAD ?? '',
    departamento: r.DEPARTAMENTO ?? '',
    empresa: r.EMPRESA ?? '',
    tipoPlan: r.TIPO_PLAN ?? '',
    // EPS / plan de salud no vienen en BeneficiarioDetalle; se dejan vacíos.
    eps: '',
    otraEps: '',
    planSalud: '',
    planNombre: '',
    estado: r.ESTADO === 'A' ? 'Activo' : 'Inactivo',
    fechaInscripcion: fechaApiAIso(r.FECHA_INGRESO),
  }
}

// Mueve al beneficiario a otro titular (por documento del titular nuevo), conservando su
// registro (plan, historial, etc.). La respuesta no trae el id del titular nuevo, así que
// el Beneficiario devuelto queda con titularId en 0 — solo sirve para leer sus datos (nombre,
// documento), no para ubicarlo bajo un titular en el estado local.
export async function cambiarTitularBeneficiario(idBeneficiario: number, documentoTitularNuevo: string): Promise<Beneficiario> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/beneficiarios/${idBeneficiario}/cambiar-titular`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify({ DOCUMENTO_TITULAR_NUEVO: documentoTitularNuevo }),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo cambiar el titular del beneficiario.')
  const data: BeneficiarioDetalleResponse = await response.json()
  return mapBeneficiarioDetalle(data, 0)
}

export async function getTitular(idTitular: number): Promise<Titular> {
  const data = await obtenerJson<TitularDetalleResponse>(
    `/api/titulares-beneficiarios/${idTitular}`,
    'No se pudo cargar el detalle del titular.',
  )
  return mapTitularDetalle(data)
}

export async function getListadoTitulares(params: ListadoTitularesParams = {}): Promise<ListadoTitulares> {
  const query = construirQueryFiltrosTitulares(params)
  if (params.limit) query.set('limit', String(params.limit))
  if (params.offset) query.set('offset', String(params.offset))
  const qs = query.toString()

  const data = await obtenerJson<ListadoTitularesResponse>(
    `/api/titulares-beneficiarios/listado${qs ? `?${qs}` : ''}`,
    'No se pudo cargar el listado de titulares.',
  )
  return {
    items: data.items.map(mapTitularListado),
    total: data.total,
    limit: data.limit,
    offset: data.offset,
  }
}

// Exporta a Excel los titulares y sus beneficiarios que cumplan los filtros activos
// (los mismos de /listado); el backend arma el .xlsx completo, acá solo se dispara la descarga.
export async function exportarTitulares(params: FiltrosTitulares = {}): Promise<Blob> {
  const qs = construirQueryFiltrosTitulares(params).toString()
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/exportar${qs ? `?${qs}` : ''}`, { headers: authHeader() })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo exportar el listado.')
  return response.blob()
}

// 4 = cupo de beneficiarios del Plan Estándar (mismo valor que CUPO_MAXIMO en
// plan-liga.constants.ts; se repite acá para no crear una dependencia circular).
const CUPO_ESTANDAR = 4

function cupoDePlan(p: PlanCatalogoResponse): number {
  const adicionales = p.BENEFICIARIOS_ADICIONALES
  if (adicionales != null && adicionales > 0) return CUPO_ESTANDAR + adicionales
  return p.MAX_BENEFICIARIOS ?? 0
}

// Catálogo de planes activos, con su cupo de beneficiarios ya resuelto: alimenta el
// selector "Plan contratado" al crear un titular (TIPO_PLAN_ID), el filtro de plan del
// listado (tipo_plan_id) y el agrupamiento titular+beneficiarios de la carga masiva.
export async function getPlanesServicio(): Promise<PlanServicio[]> {
  const data = await obtenerJson<PlanCatalogoResponse[]>(
    '/api/titulares-beneficiarios/planes',
    'No se pudo cargar la lista de planes.',
  )
  return data.map(p => ({ id: p.ID, nombre: p.NOMBRE, cupoBeneficiarios: cupoDePlan(p) }))
}

const TIPO_SEG_API: Record<TipoSeguimiento, string> = {
  Llamada: 'llamada', Correo: 'correo', Reunión: 'reunion', WhatsApp: 'whatsapp', Mensaje: 'mensaje', Nota: 'nota',
}

// El backend solo tiene "proximo_paso" como texto libre (sin campo propio para su fecha
// límite): la fecha viaja codificada como prefijo "YYYY-MM-DD::" dentro de ese mismo texto,
// mismo formato que decodifica relacionamiento.api.ts al leer la bitácora general (no se
// importa de ahí directo para no crear un ciclo: relacionamiento.api.ts ya importa de este archivo).
function codificarProximoPaso(texto: string, fechaLimite: string): string | null {
  if (!texto.trim()) return null
  return fechaLimite ? `${fechaLimite}::${texto}` : texto
}

// El endpoint de bitácora no tiene un campo propio para beneficiario_id (solo titular_id),
// así que cuando el seguimiento es sobre un beneficiario puntual, su nombre queda como
// prefijo de la descripción para poder identificarlo dentro de la bitácora del titular.
// nombre_empresa ya no es FK (mercadeo_crm_empresas): viaja como texto plano, así que se
// toma directo del titular en vez de pedirle al usuario que la busque/seleccione de nuevo.
export async function registrarSeguimiento(titular: Titular, data: SeguimientoDraft, beneficiarioNombre?: string): Promise<void> {
  const body = {
    tipo: TIPO_SEG_API[data.tipo],
    descripcion: beneficiarioNombre ? `[Beneficiario: ${beneficiarioNombre}] ${data.accion}` : data.accion,
    proximo_paso: codificarProximoPaso(data.proximoPaso, data.proximoPasoFecha),
    fecha: data.fecha,
    titular_id: titular.id,
    nombre_empresa: titular.empresa || null,
    oportunidad_id: data.oportunidadId,
    estado: data.proximoPaso.trim() ? 'pendiente' : 'realizado',
  }
  const response = await fetch(`${API_URL}/api/bitacora/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(body),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo registrar el seguimiento.')
}
