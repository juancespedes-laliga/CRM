// Cliente del backend para MailerTurbo. El backend hace de proxy hacia
// https://mailerturbo.com/apiserver (un solo endpoint con "metodo" en el body)
// y agrega ws_login + idempresa; aquí nunca se manejan esas credenciales.
//
// Backend: app/modules/integraciones/mailerturbo
//   GET  /api/mailerturbo/listas                  -> ObtenerListas
//   POST /api/mailerturbo/listas                  -> CrearLista            { titulo }
//   GET  /api/mailerturbo/plantillas              -> ListarPlantillasEmail
//   GET  /api/mailerturbo/perfiles-envio          -> ListarPerfilesEnvio
//   GET  /api/mailerturbo/campanas?pagina&por_pagina&q -> ListarCampanas
//   GET  /api/mailerturbo/campanas/{id}           -> ObtenerInfoCampana
//   GET  /api/mailerturbo/campanas/{id}/destinatarios -> ObtenerCorreosEnviadosCampana + ObtenerClicksCampana
//   GET  /api/mailerturbo/contactos/buscar?correo|telefono -> ObtenerInfoContacto
//   POST /api/mailerturbo/contactos/sincronizar   -> ObtenerInfoContacto + CrearContacto / ActualizarListasContacto
//   POST /api/mailerturbo/campanas/enviar         -> EnviarCampanaEmail
//   POST /api/mailerturbo/sesion                  -> IniciarSesion (token reutilizado hasta que vence)
import { authHeader } from '@/features/auth/composables/useAuth'
import type {
  CampanaMT, ContactoMT, DestinatarioCampanaMT, DetalleCampanaMT, EnvioCampanaMT, FiltrosAudienciaMT, InfoContactoMT, ListaMT, PaginaCampanasMT, PerfilEnvioMT,
  PlantillaMT, ResultadoEnvioCampanaMT, ResultadoSincronizacionMT, SesionMT,
} from '../types/mailerturbo'

const API_URL = import.meta.env.VITE_CRM_API_URL
const BASE = `${API_URL}/api/mailerturbo`

async function lanzarErrorConDetalle(response: Response, mensajeError: string): Promise<never> {
  if (response.status === 404) {
    throw new Error(`${mensajeError} (el backend no tiene la integración con MailerTurbo: reinícielo/actualícelo).`)
  }
  const body = await response.json().catch(() => null)
  const detail = typeof body?.detail === 'string' ? body.detail : null
  throw new Error(detail ?? mensajeError)
}

async function pedir<T>(ruta: string, mensajeError: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${ruta}`, {
      ...init,
      headers: { ...authHeader(), ...(init?.body ? { 'Content-Type': 'application/json' } : {}) },
    })
  } catch {
    throw new Error(`${mensajeError} (no hay conexión con el servidor).`)
  }
  if (!response.ok) await lanzarErrorConDetalle(response, mensajeError)
  return response.json() as Promise<T>
}

// ── Mapeos (snake_case del backend -> camelCase) ─────────────────────
interface ListaApi {
  id: number
  titulo: string
  estado: string
  total_correos: number
  total_activos: number
  total_rebotes: number
  total_salidas: number
  total_envios: number
  total_vistas: number
  total_clicks: number
  total_telefonos: number
  tipo: string | null
  fecha_creacion: string | null
}
const mapLista = (l: ListaApi): ListaMT => ({
  id: l.id,
  titulo: l.titulo,
  estado: l.estado,
  totalCorreos: l.total_correos,
  totalActivos: l.total_activos,
  totalRebotes: l.total_rebotes,
  totalSalidas: l.total_salidas,
  totalEnvios: l.total_envios,
  totalVistas: l.total_vistas,
  totalClicks: l.total_clicks,
  totalTelefonos: l.total_telefonos,
  tipo: l.tipo,
  fechaCreacion: l.fecha_creacion,
})

interface CampanaApi {
  id: number
  nombre: string
  asunto: string | null
  estado: string
  tipo: string
  fecha: string | null
  listas: string
  total_envios: number
  total_vistas: number
  porcentaje_vistas: number
  total_clicks: number
  porcentaje_clicks: number
  total_rebotes: number
  total_salidas: number
}
const mapCampana = (c: CampanaApi): CampanaMT => ({
  id: c.id,
  nombre: c.nombre,
  asunto: c.asunto,
  estado: c.estado,
  tipo: c.tipo,
  fecha: c.fecha,
  listas: c.listas,
  totalEnvios: c.total_envios,
  totalVistas: c.total_vistas,
  porcentajeVistas: c.porcentaje_vistas,
  totalClicks: c.total_clicks,
  porcentajeClicks: c.porcentaje_clicks,
  totalRebotes: c.total_rebotes,
  totalSalidas: c.total_salidas,
})

const contactoAApi = (c: ContactoMT) => ({
  nombre: c.nombre,
  apellido: c.apellido,
  correo: c.correo,
  telefono: c.telefono,
  documento: c.documento ?? null,
  ciudad: c.ciudad ?? null,
})

// ── Catálogos ────────────────────────────────────────────────────────
export async function getListas(): Promise<ListaMT[]> {
  const data = await pedir<{ listas: ListaApi[] }>('/listas', 'No se pudieron cargar las listas de MailerTurbo.')
  return data.listas.map(mapLista)
}

export async function crearLista(titulo: string): Promise<ListaMT> {
  const data = await pedir<ListaApi>('/listas', 'No se pudo crear la lista en MailerTurbo.', {
    method: 'POST',
    body: JSON.stringify({ titulo: titulo.trim() }),
  })
  return mapLista(data)
}

export async function getPlantillasMT(): Promise<PlantillaMT[]> {
  const data = await pedir<{ plantillas: PlantillaMT[] }>('/plantillas', 'No se pudieron cargar las plantillas de MailerTurbo.')
  return data.plantillas
}

export async function getPerfilesEnvio(): Promise<PerfilEnvioMT[]> {
  const data = await pedir<{ perfiles: PerfilEnvioMT[] }>('/perfiles-envio', 'No se pudieron cargar los perfiles de envío.')
  return data.perfiles
}

export async function getCampanas(pagina = 1, porPagina = 20, q = ''): Promise<PaginaCampanasMT> {
  const params = new URLSearchParams({ pagina: String(pagina), por_pagina: String(porPagina) })
  if (q.trim()) params.set('q', q.trim())
  const data = await pedir<{ campanas: CampanaApi[]; total: number; total_paginas: number }>(
    `/campanas?${params}`, 'No se pudieron cargar las campañas de MailerTurbo.',
  )
  return { campanas: data.campanas.map(mapCampana), total: data.total, totalPaginas: data.total_paginas }
}

export async function getDetalleCampana(id: number): Promise<DetalleCampanaMT> {
  const d = await pedir<{
    id: number; nombre: string; asunto: string | null; estado: string; tipo: string
    fecha: string | null; fecha_programacion: string | null; perfil_envio: string | null
    correo_perfil_envio: string | null; listas: string | null; usuario_envio: string | null
    estadisticas: Record<string, number>
  }>(`/campanas/${id}`, 'No se pudo cargar la campaña de MailerTurbo.')
  const e = d.estadisticas
  return {
    id: d.id,
    nombre: d.nombre,
    asunto: d.asunto,
    estado: d.estado,
    tipo: d.tipo,
    fecha: d.fecha,
    fechaProgramacion: d.fecha_programacion,
    perfilEnvio: d.perfil_envio,
    correoPerfilEnvio: d.correo_perfil_envio,
    listas: d.listas,
    usuarioEnvio: d.usuario_envio,
    estadisticas: {
      totalEnvios: e.total_envios,
      totalVistas: e.total_vistas,
      porcentajeVistas: e.porcentaje_vistas,
      totalClicks: e.total_clicks,
      porcentajeClicks: e.porcentaje_clicks,
      vistasLanding: e.vistas_landing,
      totalRebotes: e.total_rebotes,
      porcentajeRebotes: e.porcentaje_rebotes,
      totalSalidas: e.total_salidas,
      porcentajeSalidas: e.porcentaje_salidas,
      totalRechazados: e.total_rechazados,
    },
  }
}

/** Todos los correos de la campaña (sin paginar: la tabla pagina en el navegador). */
export async function getDestinatariosCampana(id: number): Promise<DestinatarioCampanaMT[]> {
  const data = await pedir<{
    destinatarios: {
      nombre: string; correo: string; telefono: string | null; estado_envio: string; resultado_envio: string
      fecha_enviado: string | null; abrio: boolean; fecha_apertura: string | null; clic: boolean
      fecha_clic: string | null; links: string[]; baja: boolean; fecha_baja: string | null; vista_landing: boolean
    }[]
  }>(`/campanas/${id}/destinatarios`, 'No se pudieron cargar los destinatarios de la campaña.')
  return data.destinatarios.map(x => ({
    nombre: x.nombre,
    correo: x.correo,
    telefono: x.telefono,
    estadoEnvio: x.estado_envio,
    resultadoEnvio: x.resultado_envio,
    fechaEnviado: x.fecha_enviado,
    abrio: x.abrio,
    fechaApertura: x.fecha_apertura,
    clic: x.clic,
    fechaClic: x.fecha_clic,
    links: x.links,
    baja: x.baja,
    fechaBaja: x.fecha_baja,
    vistaLanding: x.vista_landing,
  }))
}

// ── Contactos ────────────────────────────────────────────────────────
/** null si no existe. MailerTurbo no permite listar los contactos de una lista,
 * solo consultar uno por correo o teléfono. */
export async function buscarContacto(args: { correo?: string; telefono?: string }): Promise<InfoContactoMT | null> {
  const params = new URLSearchParams()
  if (args.correo?.trim()) params.set('correo', args.correo.trim())
  if (args.telefono?.trim()) params.set('telefono', args.telefono.trim())
  const data = await pedir<{
    id: number; nombre: string; apellido: string; telefono: string
    correos: { correo: string; enviar_campana: string | null; estado: string | null }[]
    campos_dinamicos: Record<string, string>
  } | null>(`/contactos/buscar?${params}`, 'No se pudo buscar el contacto en MailerTurbo.')
  if (!data) return null
  return {
    id: data.id,
    nombre: data.nombre,
    apellido: data.apellido,
    telefono: data.telefono,
    correos: data.correos.map(c => ({ correo: c.correo, enviarCampana: c.enviar_campana, estado: c.estado })),
    camposDinamicos: data.campos_dinamicos,
  }
}

/** Crea o actualiza (por correo) cada contacto y lo deja en la lista indicada. */
/** Con `audiencia`, el backend toma a todas las personas de esos filtros. */
export async function sincronizarContactos(args: {
  idLista: number
  contactos?: ContactoMT[]
  audiencia?: FiltrosAudienciaMT
  etiquetas?: string[]
}): Promise<ResultadoSincronizacionMT> {
  return pedir<ResultadoSincronizacionMT>('/contactos/sincronizar', 'No se pudieron subir los contactos a MailerTurbo.', {
    method: 'POST',
    body: JSON.stringify({
      id_lista: args.idLista,
      contactos: (args.contactos ?? []).map(contactoAApi),
      audiencia: args.audiencia ?? null,
      etiquetas: args.etiquetas ?? [],
    }),
  })
}

// ── Campañas ─────────────────────────────────────────────────────────
export async function enviarCampana(envio: EnvioCampanaMT): Promise<ResultadoEnvioCampanaMT> {
  const { contenido, destinatarios } = envio
  const data = await pedir<{ id_campana: number; explicacion: string | null; total_contactos: number | null }>(
    '/campanas/enviar', 'No se pudo crear la campaña en MailerTurbo.', {
      method: 'POST',
      body: JSON.stringify({
        nombre: envio.nombre.trim(),
        asunto: envio.asunto.trim(),
        id_perfil_envio: envio.idPerfilEnvio,
        id_plantilla: contenido.tipo === 'plantilla_mailerturbo' ? contenido.idPlantilla : null,
        html: contenido.tipo === 'html' ? contenido.html : null,
        id_listas: destinatarios.tipo === 'listas' ? destinatarios.idListas : [],
        contactos: destinatarios.tipo === 'contactos' ? destinatarios.contactos.map(contactoAApi) : [],
        audiencia: destinatarios.tipo === 'audiencia' ? destinatarios.filtros : null,
        nombre_lista: destinatarios.tipo !== 'listas' ? (destinatarios.nombreLista?.trim() || null) : null,
        id_listas_excluir: envio.idListasExcluir ?? [],
        fecha_programacion: envio.fechaProgramacion || null,
      }),
    },
  )
  return { idCampana: data.id_campana, explicacion: data.explicacion, totalContactos: data.total_contactos }
}

// ── Sesión (abrir MailerTurbo ya logueado) ───────────────────────────
export async function getSesion(): Promise<SesionMT> {
  const data = await pedir<{ tokensesion: string; fecha_expiracion: string | null; url_inicio_sesion: string }>(
    '/sesion', 'No se pudo iniciar sesión en MailerTurbo.', { method: 'POST' },
  )
  return { tokensesion: data.tokensesion, fechaExpiracion: data.fecha_expiracion, urlInicioSesion: data.url_inicio_sesion }
}

/** Abre MailerTurbo en otra pestaña con la sesión iniciada: MailerTurbo espera
 * un POST con `tokensesion`. La pestaña se abre ANTES del await para que el
 * navegador no la bloquee como ventana emergente. */
export async function abrirMailerTurbo(): Promise<void> {
  const nombreVentana = `mailerturbo-${Date.now()}`
  const ventana = window.open('about:blank', nombreVentana)
  try {
    const sesion = await getSesion()
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = sesion.urlInicioSesion
    form.target = ventana ? nombreVentana : '_blank'
    const input = document.createElement('input')
    input.type = 'hidden'
    input.name = 'tokensesion'
    input.value = sesion.tokensesion
    form.appendChild(input)
    document.body.appendChild(form)
    form.submit()
    form.remove()
  } catch (e) {
    ventana?.close()
    throw e
  }
}
