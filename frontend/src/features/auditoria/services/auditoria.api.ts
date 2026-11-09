// ─────────────────────────────────────────────────────────────────────
// API de Auditoría
//
// Contrato que espera el front (todas requieren el permiso auditoria:ver):
//
// 1. GET /api/auditoria/modulos?desde=AAAA-MM-DD&hasta=AAAA-MM-DD
//    Conteo de cambios por módulo, para el selector "Módulo a revisar".
//    → [{ modulo, total, ultimo_cambio }]
//
// 2. GET /api/auditoria/cambios?modulo=titulares,beneficiarios&desde=…&hasta=…
//      &submodulo=&buscar=&accion=&usuario=&origen=&estado=&renovado=&pagina=1&por_pagina=20
//    Log de cambios paginado: filtros, búsqueda (documento, nombre, IDs,
//    usuario) y conteos se resuelven en el servidor. "modulo" es opcional
//    (sin él trae todos) y acepta varios separados por coma.
//    → { items: CambioResponse[] (la página), total, pagina, por_pagina, truncado,
//        resumen, usuarios, estados }
//
// 3. GET /api/auditoria/cambios/{id}
//    Un cambio con su detalle completo (campos antes → después).
//    → CambioResponse
//
// 4. GET /api/auditoria/historial?modulo=titulares&registro_id=1001
//    Todo lo que se le ha hecho a un registro, del más reciente al más viejo.
//    → CambioResponse[]
//
// 5. GET /api/auditoria/renovaciones?tipo=titular|beneficiario
//    Titulares y beneficiarios de Plan Liga con su estado de renovación.
//    "tipo" es opcional (sin él trae ambos).
//    → RenovacionResponse[]
//
// Backend: app/modules/administracion/auditoria (tabla MERCADEO_CRM_AUDITORIA).
// Las fechas de los cambios llegan en UTC con zona ('…Z'); se muestran en hora local.
// ─────────────────────────────────────────────────────────────────────
import { authHeader } from '@/features/auth/composables/useAuth'
import type {
  AccionAuditoria, CampoCambiado, ModuloAuditoria, ModuloSeleccion, OrigenAuditoria,
  RegistroCambio, RenovacionRegistro, ResumenModulo, TipoPersonaPlanLiga, UsuarioAuditoria,
} from '../types/auditoria'
import { modulosDeVista } from '../constants/auditoria.constants'

const API_URL = import.meta.env.VITE_CRM_API_URL

interface CambioResponse {
  id: number
  fecha: string
  usuario_id: number
  usuario: string
  nombre_usuario: string
  rol: string | null
  ip: string | null
  accion: AccionAuditoria
  origen: OrigenAuditoria
  lote_id: string | null
  modulo: ModuloAuditoria
  registro_id: number
  registro_nombre: string
  documento: string | null
  titular: { id: number; nombre: string; documento: string } | null
  id_titular?: number | null
  id_beneficiario?: number | null
  estado_antes: string | null
  estado_despues: string | null
  fecha_inscripcion?: string | null
  fecha_registro?: string | null
  fecha_ingreso: string | null
  renovado: boolean | null
  fecha_renovado: string | null
  vigencia_hasta: string | null
  motivo: string | null
  campos: CampoCambiado[] | null
}

interface RenovacionResponse {
  tipo: TipoPersonaPlanLiga
  id: number
  nombre: string
  documento: string
  empresa: string | null
  plan: string | null
  tipo_plan?: string | null
  estado: string
  fecha_ingreso: string
  renovado: boolean
  fecha_renovado: string | null
  vencimiento: string
  renovado_por: { nombre: string; usuario: string } | null
  titular: { id: number; nombre: string } | null
}

async function lanzarErrorConDetalle(response: Response, mensajeError: string): Promise<never> {
  const body = await response.json().catch(() => null)
  const detail = typeof body?.detail === 'string' ? body.detail : null
  throw new Error(detail ?? mensajeError)
}

function mapCambio(r: CambioResponse): RegistroCambio {
  return {
    id: r.id,
    fecha: r.fecha,
    usuario: { id: r.usuario_id, usuario: r.usuario, nombre: r.nombre_usuario, rol: r.rol ?? '' },
    ip: r.ip ?? '',
    accion: r.accion,
    origen: r.origen,
    loteId: r.lote_id,
    modulo: r.modulo,
    registroId: r.registro_id,
    registroNombre: r.registro_nombre,
    documento: r.documento ?? '',
    grupoTitular: r.titular,
    idTitular: r.id_titular ?? null,
    idBeneficiario: r.id_beneficiario ?? null,
    estadoAntes: r.estado_antes,
    estadoDespues: r.estado_despues,
    fechaInscripcion: r.fecha_inscripcion ?? null,
    fechaRegistro: r.fecha_registro ?? null,
    fechaIngreso: r.fecha_ingreso,
    renovado: r.renovado,
    fechaRenovado: r.fecha_renovado,
    vigenciaHasta: r.vigencia_hasta,
    motivo: r.motivo ?? '',
    campos: r.campos ?? [],
  }
}

function mapRenovacion(r: RenovacionResponse): RenovacionRegistro {
  return {
    tipo: r.tipo,
    id: r.id,
    nombre: r.nombre,
    documento: r.documento,
    empresa: r.empresa ?? '',
    plan: r.plan ?? '',
    tipoPlan: r.tipo_plan ?? '',
    estado: r.estado,
    fechaIngreso: r.fecha_ingreso,
    renovado: r.renovado,
    fechaRenovado: r.fecha_renovado,
    vencimiento: r.vencimiento,
    ultimaRenovacionPor: r.renovado_por,
    titular: r.titular,
  }
}

function query(params: Record<string, string | number | undefined>): string {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== '') q.set(k, String(v))
  const s = q.toString()
  return s ? `?${s}` : ''
}

async function getJson<T>(path: string, mensajeError: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { headers: authHeader() })
  if (!response.ok) await lanzarErrorConDetalle(response, mensajeError)
  return response.json()
}

export interface RangoFechas { desde?: string; hasta?: string }

// 1
export async function getResumenModulos(rango: RangoFechas = {}): Promise<ResumenModulo[]> {
  const data = await getJson<{ modulo: ModuloAuditoria; total: number; ultimo_cambio: string | null }[]>(
    `/api/auditoria/modulos${query({ desde: rango.desde, hasta: rango.hasta })}`,
    'No se pudo cargar el resumen por módulo.',
  )
  return data.map(d => ({ modulo: d.modulo, total: d.total, ultimoCambio: d.ultimo_cambio }))
}

// 2
export interface ResumenCambios {
  total: number
  usuarios: number
  cambiosEstado: number
  renovaciones: number
  masivos: number
}

export interface ListadoCambios {
  /** Solo la página pedida. */
  items: RegistroCambio[]
  /** Total de cambios que cumplen los filtros (todas las páginas). */
  total: number
  /** No cupieron todos en una sola petición (solo al exportar con el tope del backend). */
  truncado: boolean
  resumen: ResumenCambios
  /** Opciones de los filtros Usuario y Estado dentro del módulo y rango de fechas. */
  usuarios: UsuarioAuditoria[]
  estados: string[]
}

/** Filtros y página que se resuelven en el servidor. */
export interface ConsultaCambios extends RangoFechas {
  submodulo?: ModuloAuditoria
  buscar?: string
  accion?: AccionAuditoria
  /** 0 = proceso automático (sin usuario). */
  usuario?: number
  origen?: OrigenAuditoria
  estado?: string
  renovado?: boolean
  pagina?: number
  porPagina?: number
}

/** Tope de filas por petición del backend (se usa al exportar todo). */
export const LIMITE_CAMBIOS = 20000

export async function getCambios(modulo: ModuloSeleccion, c: ConsultaCambios = {}): Promise<ListadoCambios> {
  const data = await getJson<{
    items: CambioResponse[]
    total: number
    truncado?: boolean
    resumen: { total: number; usuarios: number; cambios_estado: number; renovaciones: number; masivos: number }
    usuarios: { id: number; usuario: string; nombre: string }[]
    estados: string[]
  }>(
    `/api/auditoria/cambios${query({
      modulo: modulo === 'todos' ? undefined : modulosDeVista(modulo).join(','),
      desde: c.desde,
      hasta: c.hasta,
      submodulo: c.submodulo,
      buscar: c.buscar?.trim() || undefined,
      accion: c.accion,
      usuario: c.usuario,
      origen: c.origen,
      estado: c.estado,
      renovado: c.renovado === undefined ? undefined : String(c.renovado),
      pagina: c.pagina,
      por_pagina: c.porPagina,
    })}`,
    'No se pudo cargar el registro de cambios.',
  )
  return {
    items: data.items.map(mapCambio),
    total: data.total,
    truncado: !!data.truncado,
    resumen: {
      total: data.resumen.total,
      usuarios: data.resumen.usuarios,
      cambiosEstado: data.resumen.cambios_estado,
      renovaciones: data.resumen.renovaciones,
      masivos: data.resumen.masivos,
    },
    usuarios: data.usuarios.map(u => ({ ...u, rol: '' })),
    estados: data.estados,
  }
}

// 3
export async function getCambio(id: number): Promise<RegistroCambio> {
  return mapCambio(await getJson<CambioResponse>(`/api/auditoria/cambios/${id}`, 'No se pudo cargar el detalle del cambio.'))
}

// 4
export async function getHistorial(modulo: ModuloAuditoria, registroId: number): Promise<RegistroCambio[]> {
  const data = await getJson<CambioResponse[]>(
    `/api/auditoria/historial${query({ modulo, registro_id: registroId })}`,
    'No se pudo cargar el historial.',
  )
  return data.map(mapCambio)
}

// 5
export async function getRenovaciones(tipo?: TipoPersonaPlanLiga): Promise<RenovacionRegistro[]> {
  const data = await getJson<RenovacionResponse[]>(
    `/api/auditoria/renovaciones${query({ tipo })}`,
    'No se pudo cargar el listado de renovaciones.',
  )
  return data.map(mapRenovacion)
}
