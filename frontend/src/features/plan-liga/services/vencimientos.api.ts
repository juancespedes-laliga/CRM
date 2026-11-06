import { authHeader } from '@/features/auth/composables/useAuth'

const API_URL = import.meta.env.VITE_CRM_API_URL

export interface TitularPorVencer {
  ID: number
  TIPO: string | null
  DOCUMENTO: string | null
  NOMBRE: string | null
  CORREO: string | null
  TELEFONO: string | null
  EMPRESA: string | null
  TIPO_PLAN: string | null
  FECHA_INGRESO: string | null
  FECHA_FIN: string | null
  DIAS: number
  FECHA_FIN_TXT: string
  RENOVADO: string | null
  VENCIDO: boolean
  YA_ENVIADO: boolean
}

export interface EstadoUltimoEnvio {
  ultimo_envio: string | null
  ultimo_total: number | null
  ultimo_enviados: number | null
  ultimo_fallidos: number | null
  ejecutado_por: string | null
  dias_previos: number | null
  dias_vencidos: number | null
  cubierto_desde: string | null
  cubierto_hasta: string | null
}

export interface ListadoPorVencer {
  total: number
  nuevos: number
  ya_enviados: number
  dias_previos: number
  dias_vencidos: number
  estado_envio: EstadoUltimoEnvio
  items: TitularPorVencer[]
}

export interface FalloEnvio {
  DOCUMENTO: string | null
  NOMBRE: string | null
  CORREO: string | null
  error: string
}

export interface EnvioResultado {
  total: number
  a_enviar: number
  enviados: number
  fallidos: number
  omitidos_ya_enviados: number
  fallos: FalloEnvio[]
  estado_envio: EstadoUltimoEnvio
}

interface Opciones {
  diasPrevios?: number
  diasVencidos?: number
  incluirYaEnviados?: boolean
}

async function parseError(response: Response, fallback: string): Promise<never> {
  const body = await response.json().catch(() => null)
  const detail = typeof body?.detail === 'string' ? body.detail : null
  throw new Error(detail ?? fallback)
}

// Titulares particulares (sin empresa asociada): es el flujo de siempre, con
// envío automático a su propio correo.
export async function getPorVencer(opts: Opciones = {}): Promise<ListadoPorVencer> {
  const params = new URLSearchParams({
    dias_previos: String(opts.diasPrevios ?? 7),
    dias_vencidos: String(opts.diasVencidos ?? 0),
    solo_con_correo: 'true',
    segmento: 'particular',
  })
  const response = await fetch(
    `${API_URL}/api/correos/vencimiento/pendientes?${params}`,
    { headers: authHeader() },
  )
  if (!response.ok) await parseError(response, 'No se pudo cargar la lista de próximos a vencer.')
  return response.json()
}

export async function enviarRecordatorios(opts: Opciones = {}): Promise<EnvioResultado> {
  const params = new URLSearchParams({
    dias_previos: String(opts.diasPrevios ?? 7),
    dias_vencidos: String(opts.diasVencidos ?? 0),
    incluir_ya_enviados: String(opts.incluirYaEnviados ?? false),
  })
  const response = await fetch(
    `${API_URL}/api/correos/vencimiento/enviar?${params}`,
    { method: 'POST', headers: authHeader() },
  )
  if (!response.ok) await parseError(response, 'No se pudieron enviar los recordatorios.')
  return response.json()
}

export interface HistorialEnvioItem {
  fecha: string | null
  enviados: number
  fallidos: number
  total: number
  ejecutado_por: string | null
  dias_previos: number | null
  dias_vencidos: number | null
  fallos: FalloEnvio[]
}

export async function getHistorialEnvios(limit = 20): Promise<HistorialEnvioItem[]> {
  const response = await fetch(
    `${API_URL}/api/correos/vencimiento/historial?limit=${limit}`,
    { headers: authHeader() },
  )
  if (!response.ok) await parseError(response, 'No se pudo cargar el historial de envíos.')
  return response.json()
}

// ---------------------------------------------------------------------------
// Empresas (convenio Plan Liga Empresarial): agrupado por empresa. SOLO
// consulta — desde el CRM no se envían correos a las empresas.
// ---------------------------------------------------------------------------

export interface EmpresaPorVencer {
  EMPRESA: string
  TOTAL: number
  titulares: TitularPorVencer[]
}

export interface ListadoEmpresasPorVencer {
  total_empresas: number
  total_titulares: number
  dias_previos: number
  dias_vencidos: number
  empresas: EmpresaPorVencer[]
}

export async function getEmpresasPorVencer(opts: Opciones = {}): Promise<ListadoEmpresasPorVencer> {
  const params = new URLSearchParams({
    dias_previos: String(opts.diasPrevios ?? 7),
    dias_vencidos: String(opts.diasVencidos ?? 0),
  })
  const response = await fetch(
    `${API_URL}/api/correos/vencimiento/empresas?${params}`,
    { headers: authHeader() },
  )
  if (!response.ok) await parseError(response, 'No se pudo cargar la lista de empresas por vencer.')
  return response.json()
}
