import { authHeader } from '@/features/auth/composables/useAuth'
import type { FiltroSegmento } from '../constants/ciclo-afiliado.constants'

const API_URL = import.meta.env.VITE_CRM_API_URL

export interface AudienciaItemApi {
  IDENTIFICACION: string | null
  NOMBRES: string | null
  EMPRESA: string | null
  SEXO: string | null
  EDAD: number | null
  CIUDAD: string | null
  DEPARTAMENTO: string | null
  CORREO: string | null
  TELEFONO: string | null
  TIPO_PLAN: string | null
  CONCEPTO: string | null
  SERVICIO: string | null
  ESPECIALIDAD: string | null
  SERVICIOS_USADOS: number | null
  ULTIMO_USO: string | null
  TIPO_VINCULACION: string | null
}

export interface ListadoAudienciaApi {
  total: number
  items: AudienciaItemApi[]
}

/** Trae los valores distintos de TMPBI1 para poblar un desplegable de filtro
 * (el backend los cachea un rato, TMPBI1 tiene millones de filas). */
async function getValoresDistintos(recurso: 'ciudades' | 'conceptos' | 'servicios'): Promise<string[]> {
  const response = await fetch(`${API_URL}/api/segmentos/${recurso}`, {
    headers: authHeader(),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, `No se pudo cargar ${recurso}.`)
  const data = (await response.json()) as { valores: string[] }
  return data.valores
}

export const getCiudades = (): Promise<string[]> => getValoresDistintos('ciudades')
export const getConceptos = (): Promise<string[]> => getValoresDistintos('conceptos')
export const getServicios = (): Promise<string[]> => getValoresDistintos('servicios')

export interface UbicacionApi {
  departamento: string
  municipio: string
}

/** Pares (departamento, municipio) distintos de TMPBI1, para el desplegable
 * en cascada Departamento -> Ciudad/municipio. */
export async function getUbicaciones(): Promise<UbicacionApi[]> {
  const response = await fetch(`${API_URL}/api/segmentos/ubicaciones`, {
    headers: authHeader(),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudieron cargar las ubicaciones.')
  const data = (await response.json()) as { ubicaciones: UbicacionApi[] }
  return data.ubicaciones
}

export interface ConceptoServicioApi {
  concepto: string
  servicio: string
}

/** Pares (concepto, servicio) distintos de TMPBI1, para el desplegable en
 * cascada Concepto -> Servicio. */
export async function getConceptosServicios(): Promise<ConceptoServicioApi[]> {
  const response = await fetch(`${API_URL}/api/segmentos/conceptos-servicios`, {
    headers: authHeader(),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudieron cargar los conceptos/servicios.')
  const data = (await response.json()) as { pares: ConceptoServicioApi[] }
  return data.pares
}

export interface CategoriaUsoPlan {
  activos: number
  conUso: number
  sinUso: number
  porcentajeUso: number
}

export interface ResumenUsoPlan {
  total: CategoriaUsoPlan
  titulares: CategoriaUsoPlan
  beneficiarios: CategoriaUsoPlan
}

interface CategoriaUsoPlanApi {
  activos: number
  con_uso: number
  sin_uso: number
  porcentaje_uso: number
}

function mapCategoriaUsoPlan(c: CategoriaUsoPlanApi): CategoriaUsoPlan {
  return { activos: c.activos, conUso: c.con_uso, sinUso: c.sin_uso, porcentajeUso: c.porcentaje_uso }
}

/** Resumen de uso de Plan Liga: titulares/beneficiarios activos, cuantos han
 * usado el plan (TMPBI1.TARIFA='PL') y cuantos no, total y por separado. */
export async function getResumenUsoPlan(): Promise<ResumenUsoPlan> {
  const response = await fetch(`${API_URL}/api/segmentos/uso-plan/resumen`, {
    headers: authHeader(),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo cargar el resumen de uso del plan.')
  const data = (await response.json()) as {
    total: CategoriaUsoPlanApi
    titulares: CategoriaUsoPlanApi
    beneficiarios: CategoriaUsoPlanApi
  }
  return {
    total: mapCategoriaUsoPlan(data.total),
    titulares: mapCategoriaUsoPlan(data.titulares),
    beneficiarios: mapCategoriaUsoPlan(data.beneficiarios),
  }
}

export interface UsoPlanPersona {
  documento: string
  tipo: 'titular' | 'beneficiario'
  nombre: string
  estado: string
  haUsado: boolean
  serviciosUsados: number
  ultimoUso: string | null
}

/** Busca un documento como titular o beneficiario y dice si ha usado el plan.
 * Lanza si no existe (404) o si el request falla. */
export async function buscarUsoPlan(documento: string): Promise<UsoPlanPersona> {
  const response = await fetch(
    `${API_URL}/api/segmentos/uso-plan/buscar?documento=${encodeURIComponent(documento.trim())}`,
    { headers: authHeader() },
  )
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo buscar el documento.')
  const data = await response.json() as {
    documento: string
    tipo: 'titular' | 'beneficiario'
    nombre: string
    estado: string
    ha_usado: boolean
    servicios_usados: number
    ultimo_uso: string | null
  }
  return {
    documento: data.documento,
    tipo: data.tipo,
    nombre: data.nombre,
    estado: data.estado,
    haUsado: data.ha_usado,
    serviciosUsados: data.servicios_usados,
    ultimoUso: data.ultimo_uso,
  }
}

/** Fila de la tabla de Audiencias (mapeo del consolidado). */
export interface PersonaAudiencia {
  id: string
  nombre: string
  documento: string
  sexo: string | null
  edad: number | null
  empresa: string | null
  direccion: string
  plan: string
  vinculacion: string
  concepto: string | null
  servicio: string | null
  especialidad: string | null
  ultimoUsoDias: number | null
  nServicios: number
  tieneCorreo: boolean
  tieneCelular: boolean
  correo: string | null
  telefono: string | null
}

async function lanzarErrorConDetalle(response: Response, mensajeError: string): Promise<never> {
  const body = await response.json().catch(() => null)
  const detail = typeof body?.detail === 'string' ? body.detail : null
  throw new Error(detail ?? mensajeError)
}

function diasDesde(fechaIso: string | null): number | null {
  if (!fechaIso) return null
  const fecha = new Date(`${fechaIso}T00:00:00`)
  if (Number.isNaN(fecha.getTime())) return null
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  return Math.max(0, Math.floor((hoy.getTime() - fecha.getTime()) / 86_400_000))
}

export function mapAudienciaItem(item: AudienciaItemApi): PersonaAudiencia {
  const documento = (item.IDENTIFICACION ?? '').trim()
  const ciudad = (item.CIUDAD ?? '').trim()
  const depto = (item.DEPARTAMENTO ?? '').trim()
  const direccion = [ciudad, depto].filter(Boolean).join(' · ') || '—'
  return {
    id: documento || `${item.NOMBRES ?? 'sin-id'}-${item.ULTIMO_USO ?? ''}`,
    nombre: (item.NOMBRES ?? '').trim() || 'Sin nombre',
    documento,
    sexo: item.SEXO,
    edad: item.EDAD,
    empresa: item.EMPRESA,
    direccion,
    plan: (item.TIPO_PLAN ?? '').trim() || '—',
    vinculacion: (item.TIPO_VINCULACION ?? '').trim() || '—',
    concepto: item.CONCEPTO,
    servicio: item.SERVICIO,
    especialidad: item.ESPECIALIDAD,
    ultimoUsoDias: diasDesde(item.ULTIMO_USO),
    nServicios: item.SERVICIOS_USADOS ?? 0,
    tieneCorreo: Boolean(item.CORREO?.trim()),
    tieneCelular: Boolean(item.TELEFONO?.trim()),
    correo: item.CORREO,
    telefono: item.TELEFONO,
  }
}

/** Traduce el filtro de Embudos a query params de GET /api/segmentos/audiencias. */
export function filtroSegmentoAQuery(
  f: FiltroSegmento,
  pagina = 1,
  porPagina = 10,
): URLSearchParams {
  const q = new URLSearchParams()

  if (f.planLiga === 'No plan Liga') q.set('plan', 'no_plan_liga')
  else q.set('plan', 'plan_liga')

  // Solo tiene efecto junto con plan_liga (ver descripcion en el backend);
  // si el usuario lo dejo marcado y despues cambio a 'No plan Liga', se
  // manda igual pero el backend simplemente lo ignora.
  if (f.usoPlan === 'con_uso' || f.usoPlan === 'sin_uso') q.set('uso_plan', f.usoPlan)

  if (f.sexo === 'F' || f.sexo === 'M') q.set('sexo', f.sexo)

  // String(...) primero: los inputs son type="number", y Vue convierte
  // v-model a Number automaticamente en ese caso (aunque el tipo declarado
  // de FiltroSegmento diga string) -- f.edadMin puede llegar aqui como
  // numero real, no como string.
  const edadMinTexto = String(f.edadMin ?? '').trim()
  const edadMaxTexto = String(f.edadMax ?? '').trim()
  const edadMin = edadMinTexto === '' ? null : Number(edadMinTexto)
  const edadMax = edadMaxTexto === '' ? null : Number(edadMaxTexto)
  if (edadMin !== null && !Number.isNaN(edadMin)) q.set('edad_min', String(edadMin))
  if (edadMax !== null && !Number.isNaN(edadMax)) q.set('edad_max', String(edadMax))

  // Departamento y ciudad: desplegables de una sola opcion, en cascada
  // (ver FiltrosSegmento.vue).
  if (f.departamento) q.set('departamento', f.departamento.toUpperCase())
  if (f.ciudades.length) q.set('ciudad', f.ciudades[0].toUpperCase())
  if (f.conceptos.length) q.set('concepto', f.conceptos[0])
  if (f.servicios.length) q.set('servicio', f.servicios[0])

  if (f.vinculacion === 'Particular') q.set('tipo_vinculacion', 'particular')
  else if (f.vinculacion === 'Empresa') q.set('tipo_vinculacion', 'empresa')

  if (f.ultimoUso === '90' || f.ultimoUso === '60' || f.ultimoUso === '30') {
    q.set('ultimo_uso', f.ultimoUso)
  }

  q.set('pagina', String(pagina))
  q.set('por_pagina', String(porPagina))

  return q
}

/** Trae una sola pagina (util para paginacion real del backend). */
export async function getAudiencias(
  f: FiltroSegmento,
  pagina = 1,
  porPagina = 10,
): Promise<{ total: number; items: PersonaAudiencia[] }> {
  const params = filtroSegmentoAQuery(f, pagina, porPagina)
  const response = await fetch(`${API_URL}/api/segmentos/audiencias?${params}`, {
    headers: authHeader(),
  })
  if (!response.ok) await lanzarErrorConDetalle(response, 'No se pudo cargar la audiencia.')
  const data = (await response.json()) as ListadoAudienciaApi
  return { total: data.total, items: data.items.map(mapAudienciaItem) }
}

// Se carga de a BLOQUES (no toda la audiencia de una vez): solo el bloque
// que el usuario esta viendo; si avanza mas alla, ahi se pide el siguiente.
//
// HILOS_POR_BLOQUE = 1 (sin paralelismo real) a proposito: TMPBI1 tiene
// ~5.17 millones de filas, y con una tabla de ese tamaño varias consultas
// simultaneas no "reparten" el trabajo, compiten por el mismo I/O y CPU de
// Oracle y terminan mas lentas que una sola (medido: 300 filas solas = 7s,
// 4 en paralelo = 30s+). El cuello de botella es el tamaño de la tabla, no
// la falta de paralelismo del lado del cliente.
export const TAMANO_BLOQUE = 500
const HILOS_POR_BLOQUE = 1
const TAMANO_HILO = TAMANO_BLOQUE / HILOS_POR_BLOQUE

/**
 * Trae el bloque `indiceBloque` (0 = primeras 500, 1 = las siguientes 500,
 * etc.), dividido en HILOS_POR_BLOQUE peticiones paralelas. Devuelve el
 * total real de la audiencia (igual en cualquier bloque) y las filas de
 * este bloque, en el orden correcto (ULTIMO_USO DESC) aunque las peticiones
 * de los hilos no terminen en orden.
 */
export async function getBloqueAudiencia(
  f: FiltroSegmento,
  indiceBloque: number,
): Promise<{ total: number; items: PersonaAudiencia[] }> {
  const inicioBloque = indiceBloque * TAMANO_BLOQUE
  const hilos = Array.from({ length: HILOS_POR_BLOQUE }, (_, h) => h)

  // pagina/por_pagina del backend calculan offset = (pagina-1)*por_pagina;
  // con por_pagina = TAMANO_HILO, la pagina que corresponde a cada hilo es:
  const paginaDeHilo = (h: number) => (inicioBloque + h * TAMANO_HILO) / TAMANO_HILO + 1

  // Promise.all conserva el orden de "hilos" en el resultado (no el orden
  // en que cada peticion termina), asi que el orden final de las filas
  // queda igual que si se hubieran pedido una por una.
  const resultados = await Promise.all(
    hilos.map(h => getAudiencias(f, paginaDeHilo(h), TAMANO_HILO)),
  )
  const total = resultados[0]?.total ?? 0
  const items = resultados.flatMap(r => r.items)
  return { total, items }
}
