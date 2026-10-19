// Tipos del módulo MailerTurbo (proveedor de correo masivo).
// El frontend NUNCA habla directo con MailerTurbo: las credenciales (wsUsr,
// wsPass, wsKey, idempresa) viven solo en el backend, que expone /api/mailerturbo/*.

export interface ListaMT {
  id: number
  titulo: string
  estado: string
  totalCorreos: number
  totalActivos: number
  totalRebotes: number
  totalSalidas: number
  totalEnvios: number
  totalVistas: number
  totalClicks: number
  totalTelefonos: number
  tipo: string | null
  fechaCreacion: string | null
}

/** Contacto tal como está en MailerTurbo (búsqueda por correo o teléfono). */
export interface InfoContactoMT {
  id: number
  nombre: string
  apellido: string
  telefono: string
  correos: { correo: string; enviarCampana: string | null; estado: string | null }[]
  camposDinamicos: Record<string, string>
}

export interface PlantillaMT {
  id: number
  nombre: string
}

export interface PerfilEnvioMT {
  id: number
  titulo: string
  correo: string
  estado: string
}

export interface CampanaMT {
  id: number
  nombre: string
  asunto: string | null
  estado: string
  tipo: string
  fecha: string | null
  listas: string
  totalEnvios: number
  totalVistas: number
  porcentajeVistas: number
  totalClicks: number
  porcentajeClicks: number
  totalRebotes: number
  totalSalidas: number
}

export interface PaginaCampanasMT {
  campanas: CampanaMT[]
  total: number
  totalPaginas: number
}

export interface EstadisticasCampanaMT {
  totalEnvios: number
  totalVistas: number
  porcentajeVistas: number
  totalClicks: number
  porcentajeClicks: number
  vistasLanding: number
  totalRebotes: number
  porcentajeRebotes: number
  totalSalidas: number
  porcentajeSalidas: number
  totalRechazados: number
}

export interface DetalleCampanaMT {
  id: number
  nombre: string
  asunto: string | null
  estado: string
  tipo: string
  fecha: string | null
  fechaProgramacion: string | null
  perfilEnvio: string | null
  correoPerfilEnvio: string | null
  listas: string | null
  usuarioEnvio: string | null
  estadisticas: EstadisticasCampanaMT
}

/** Un correo de la campaña con su resultado. */
export interface DestinatarioCampanaMT {
  nombre: string
  correo: string
  telefono: string | null
  /** 'Enviado' u otro estado de MailerTurbo (pendiente, cancelado…). */
  estadoEnvio: string
  /** 'Normal' | 'Rebote' | 'Baja' | 'Rechazado'… */
  resultadoEnvio: string
  fechaEnviado: string | null
  abrio: boolean
  fechaApertura: string | null
  clic: boolean
  fechaClic: string | null
  links: string[]
  baja: boolean
  fechaBaja: string | null
  vistaLanding: boolean
}

/** Persona que se sube/envía a MailerTurbo (desde Audiencias, un Excel/CSV, etc.). */
export interface ContactoMT {
  nombre: string
  apellido: string
  correo: string
  telefono: string
  documento?: string
  ciudad?: string
}

export interface ResultadoSincronizacionMT {
  total: number
  creados: number
  actualizados: number
  fallidos: number
  fallos: { correo: string; error: string }[]
}

/** De dónde sale el contenido del correo. */
export type ContenidoCampanaMT =
  | { tipo: 'plantilla_mailerturbo'; idPlantilla: number }
  | { tipo: 'html'; html: string }

/** Filtros de Audiencias (mismos de GET /api/segmentos/audiencias, sin paginación):
 * con "Seleccionar toda la audiencia" el backend arma la lista completa. */
export interface FiltrosAudienciaMT {
  plan?: string
  uso_plan?: string
  sexo?: string
  edad_min?: number
  edad_max?: number
  ciudad?: string
  departamento?: string
  concepto?: string
  servicio?: string
  tipo_vinculacion?: string
  ultimo_uso?: string
  /** Documentos desmarcados a mano después de "Seleccionar todo". */
  excluir_documentos?: string[]
}

/** Toda la audiencia de un filtro (la resuelve el backend). */
export interface AudienciaCompletaMT {
  filtros: FiltrosAudienciaMT
  /** Personas en la audiencia (antes de descartar las que no tienen correo). */
  total: number
}

/** De dónde salen los destinatarios. */
export type DestinatariosCampanaMT =
  | { tipo: 'listas'; idListas: number[] }
  | { tipo: 'contactos'; contactos: ContactoMT[]; nombreLista?: string }
  | { tipo: 'audiencia'; filtros: FiltrosAudienciaMT; nombreLista?: string }

export interface EnvioCampanaMT {
  nombre: string
  asunto: string
  idPerfilEnvio: number
  contenido: ContenidoCampanaMT
  destinatarios: DestinatariosCampanaMT
  idListasExcluir?: number[]
  /** 'YYYY-MM-DD HH:mm' o null para enviar de inmediato. */
  fechaProgramacion?: string | null
}

export interface ResultadoEnvioCampanaMT {
  idCampana: number
  explicacion: string | null
  /** Contactos con correo válido que se mandaron (null si fue a listas). */
  totalContactos: number | null
}

export interface SesionMT {
  tokensesion: string
  fechaExpiracion: string | null
  urlInicioSesion: string
}
