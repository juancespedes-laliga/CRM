import type { Actividad, ActividadDraft, TipoActividad } from '../types/actividad'
import { getTitular } from '@/features/plan-liga/services/plan-liga.api'
import { authHeader } from '@/features/auth/composables/useAuth'

const API_URL = import.meta.env.VITE_CRM_API_URL

// Forma cruda de GET /api/bitacora/: paginada (items/total), snake_case. Trae contacto_nombre/
// usuario_nombre ya resueltos, pero no titular_nombre. nombre_empresa ya no es FK (no hay
// empresa_id): es texto libre, tal cual se escribió al crear el registro.
interface BitacoraApiItem {
  id: number
  tipo: string
  descripcion: string
  proximo_paso: string | null
  fecha: string
  estado: string
  usuario_id: number | null
  usuario_nombre: string | null
  contacto_id: number | null
  contacto_nombre: string | null
  contacto_documento: string | null
  nombre_empresa: string | null
  oportunidad_id: number | null
  titular_id: number | null
  titular_documento: string | null
  fecha_actualizacion: string | null
  usuario_actualizacion_nombre: string | null
}

interface BitacoraListadoResponse {
  items: BitacoraApiItem[]
  total: number
  conteo_por_tipo: Record<string, number>
}

// El "tipo" que guarda el backend no es consistente en mayúsculas/tildes (ej. "Llamada",
// "Reunion", "nota" conviven en datos reales), así que la búsqueda se normaliza antes de mapear.
const normalizarTipo = (tipo: string) => tipo
  .toLowerCase()
  .normalize('NFD').replace(/[̀-ͯ]/g, '')

const TIPO_DESDE_API: Record<string, TipoActividad> = {
  llamada: 'Llamada', correo: 'Correo', reunion: 'Reunión', whatsapp: 'WhatsApp', mensaje: 'Mensaje', nota: 'Nota',
}
const TIPO_A_API: Record<TipoActividad, string> = {
  Llamada: 'llamada', Correo: 'correo', Reunión: 'reunion', WhatsApp: 'whatsapp', Mensaje: 'mensaje', Nota: 'nota',
}

async function lanzarErrorConDetalle(response: Response, mensajeError: string): Promise<never> {
  const body = await response.json().catch(() => null)
  const detail = typeof body?.detail === 'string' ? body.detail : null
  throw new Error(detail ?? mensajeError)
}

// El backend solo tiene "proximo_paso" como texto libre (sin un campo propio para su fecha
// límite), así que la fecha viaja codificada como prefijo "YYYY-MM-DD::" dentro de ese mismo
// texto. Es el mismo truco que ya usa plan-liga.api.ts para colar el nombre del beneficiario
// dentro de "descripcion" cuando el backend tampoco tiene un campo dedicado.
const RE_PROXIMO_PASO_FECHA = /^(\d{4}-\d{2}-\d{2})::/

function codificarProximoPaso(texto: string, fechaLimite: string): string | null {
  if (!texto.trim()) return null
  return fechaLimite ? `${fechaLimite}::${texto}` : texto
}

function decodificarProximoPaso(raw: string | null): { proximoPaso: string; proximoPasoFecha: string } {
  if (!raw) return { proximoPaso: '', proximoPasoFecha: '' }
  const match = raw.match(RE_PROXIMO_PASO_FECHA)
  if (!match) return { proximoPaso: raw, proximoPasoFecha: '' }
  return { proximoPaso: raw.slice(match[0].length), proximoPasoFecha: match[1] }
}

// El endpoint no trae titular_nombre; se resuelve aparte con Plan Liga, que sí está
// conectado al backend real.
async function resolverTitularNombre(titularId: number | null): Promise<string> {
  if (titularId === null) return ''
  try {
    return (await getTitular(titularId)).nombre
  } catch {
    return ''
  }
}

function mapItem(r: BitacoraApiItem, titularNombre: string): Actividad {
  const { proximoPaso, proximoPasoFecha } = decodificarProximoPaso(r.proximo_paso)
  return {
    id: r.id,
    tipo: TIPO_DESDE_API[normalizarTipo(r.tipo)] ?? 'Nota',
    contactoId: r.contacto_id,
    contactoNombre: r.contacto_nombre ?? '',
    contactoDocumento: r.contacto_documento ?? '',
    empresaNombre: r.nombre_empresa ?? '',
    titularId: r.titular_id,
    titularNombre,
    titularDocumento: r.titular_documento ?? '',
    accion: r.descripcion,
    proximoPaso,
    proximoPasoFecha,
    fecha: r.fecha.split('T')[0],
    usuario: r.usuario_nombre ?? '',
    oportunidadId: r.oportunidad_id,
    estado: r.estado === 'realizado' ? 'realizado' : 'pendiente',
    usuarioActualizacion: r.usuario_actualizacion_nombre ?? '',
    fechaActualizacion: r.fecha_actualizacion ? r.fecha_actualizacion.split('T')[0] : '',
  }
}

// El backend limita "limit" a un máximo de 6 por pedido (igual que /api/contactos/), así
// que para traer la bitácora completa se pagina en bucle de a 6 hasta que una página vuelve
// con menos de 6 (ahí se acaba). El filtrado/búsqueda de la página y el panel de Pendientes
// siguen operando en el cliente sobre el listado completo ya cargado.
const LIMITE_POR_PAGINA = 6
const MAX_PAGINAS = 500

export async function getActividades(): Promise<Actividad[]> {
  const items: BitacoraApiItem[] = []
  for (let pagina = 0; pagina < MAX_PAGINAS; pagina++) {
    const skip = pagina * LIMITE_POR_PAGINA
    const response = await fetch(`${API_URL}/api/bitacora/?skip=${skip}&limit=${LIMITE_POR_PAGINA}`, { headers: authHeader() })
    if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo cargar la bitácora.')
    const bloque: BitacoraListadoResponse = await response.json()
    items.push(...bloque.items)
    if (bloque.items.length < LIMITE_POR_PAGINA) break
  }

  const titularIds = [...new Set(items.map(d => d.titular_id).filter((id): id is number => id !== null))]
  const nombresPorTitular = new Map<number, string>()
  await Promise.all(titularIds.map(async (id) => { nombresPorTitular.set(id, await resolverTitularNombre(id)) }))

  return items
    .map(r => mapItem(r, r.titular_id !== null ? (nombresPorTitular.get(r.titular_id) ?? '') : ''))
    .sort((a, b) => b.fecha.localeCompare(a.fecha))
}

function construirBody(data: ActividadDraft) {
  return {
    tipo: TIPO_A_API[data.tipo],
    descripcion: data.accion,
    proximo_paso: codificarProximoPaso(data.proximoPaso, data.proximoPasoFecha),
    fecha: data.fecha,
    contacto_id: data.contactoId,
    nombre_empresa: data.empresaNombre || null,
    titular_id: data.titularId,
    oportunidad_id: data.oportunidadId,
    estado: data.proximoPaso.trim() ? 'pendiente' : 'realizado',
  }
}

export async function createActividad(data: ActividadDraft): Promise<void> {
  const response = await fetch(`${API_URL}/api/bitacora/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(construirBody(data)),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo registrar la actividad.')
}

export async function updateActividad(id: number, data: ActividadDraft): Promise<void> {
  const response = await fetch(`${API_URL}/api/bitacora/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(construirBody(data)),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo actualizar la actividad.')
}

// Marca la actividad como realizada sin tocar el resto de sus campos (PATCH dedicado,
// más directo que reutilizar el PUT completo con el próximo paso vacío).
export async function completarActividad(id: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/bitacora/${id}/completar`, {
    method: 'PATCH',
    headers: { ...authHeader() },
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo marcar la actividad como realizada.')
}

export async function deleteActividad(id: number): Promise<void> {
  const response = await fetch(`${API_URL}/api/bitacora/${id}`, {
    method: 'DELETE',
    headers: { ...authHeader() },
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo eliminar la actividad.')
}
