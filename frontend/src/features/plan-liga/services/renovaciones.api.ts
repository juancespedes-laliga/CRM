import { authHeader } from '@/features/auth/composables/useAuth'

const API_URL = import.meta.env.VITE_CRM_API_URL

export interface RenovacionMesItem {
  ID: number
  TIPO_DOCUMENTO: string | null
  DOCUMENTO: string
  NOMBRE: string
  CORREO: string | null
  TELEFONO: string | null
  EMPRESA: string | null
  TIPO_PLAN: string | null
  ESTADO: string
  RENOVADO: string | null
  FECHA_INGRESO: string
  FECHA_FIN: string
  ULTIMO_CONTACTO_FECHA: string | null
  ULTIMO_CONTACTO_DESC: string | null
  // Color que el equipo le asigna a mano a la fila (compartido: lo guarda el
  // backend, no es local a este navegador). null = sin colorear.
  COLOR: string | null
}

export interface ResumenRenovacionesMes {
  anio: number
  mes: number
  total: number
  renovados: number
  altas_nuevas: number
  activos: number
  inactivos: number
  vencen: number
}

export interface ListadoRenovacionesMes {
  resumen: ResumenRenovacionesMes
  items: RenovacionMesItem[]
  // Titulares activos cuyo plan vence (ingreso + 12 meses) en ese mes.
  vencen: RenovacionMesItem[]
}

async function parseError(response: Response, fallback: string): Promise<never> {
  const body = await response.json().catch(() => null)
  const detail = typeof body?.detail === 'string' ? body.detail : null
  throw new Error(detail ?? fallback)
}

// Titulares cuyo FECHA_INGRESO cae en ese mes/año (se activaron o renovaron
// ese mes) -- RENOVADO distingue renovación de alta nueva.
export async function getRenovacionesMes(anio: number, mes: number): Promise<ListadoRenovacionesMes> {
  const params = new URLSearchParams({ anio: String(anio), mes: String(mes) })
  const response = await fetch(
    `${API_URL}/api/titulares-beneficiarios/renovaciones?${params}`,
    { headers: authHeader() },
  )
  if (!response.ok) await parseError(response, 'No se pudo cargar las renovaciones del mes.')
  return response.json()
}

// color=null quita el color de la fila.
export async function actualizarColorTitular(idTitular: number, color: string | null): Promise<void> {
  const response = await fetch(`${API_URL}/api/titulares-beneficiarios/${idTitular}/color`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify({ COLOR: color }),
  })
  if (!response.ok) await parseError(response, 'No se pudo actualizar el color.')
}
