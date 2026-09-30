export type TipoActividad = 'Llamada' | 'Correo' | 'Reunión' | 'WhatsApp' | 'Mensaje' | 'Nota'
export type EstadoActividad = 'pendiente' | 'realizado'

export interface Actividad {
  id: number
  tipo: TipoActividad
  contactoId: number | null
  contactoNombre: string
  /** Cédula/NIT del contacto asociado; '' si no tiene contacto o el contacto no tiene documento. */
  contactoDocumento: string
  /** Texto libre (no FK): el backend ya no valida contra un catálogo de empresas. */
  empresaNombre: string
  /** Titular Plan Liga asociado a la actividad; opcional, igual que contacto y empresa. */
  titularId: number | null
  titularNombre: string
  /** Cédula del titular Plan Liga asociado; '' si no tiene titular. */
  titularDocumento: string
  accion: string
  proximoPaso: string
  /** Fecha límite del próximo paso; '' si no se definió una. No es un campo propio del
   *  backend (solo tiene "proximo_paso" como texto), se codifica dentro de ese mismo texto. */
  proximoPasoFecha: string
  fecha: string
  /** Quien registró la actividad; lo resuelve el backend a partir del usuario autenticado
   *  (Bearer token), no es un campo que el formulario deje elegir. */
  usuario: string
  /** Oportunidad a la que queda ligada la actividad; null si aún no tiene una oportunidad asociada. */
  oportunidadId: number | null
  /** Deriva del backend a partir de si hay próximo paso pendiente; no es un campo que el
   *  formulario deje editar directamente (ver construirBody en relacionamiento.api.ts). Se
   *  puede cambiar a 'realizado' sin tocar el resto vía completarActividad(). */
  estado: EstadoActividad
  /** Quien hizo el último cambio (editar/completar), y cuándo. '' si nunca se ha editado. */
  usuarioActualizacion: string
  fechaActualizacion: string
}

export type ActividadDraft = Omit<
  Actividad,
  'id' | 'usuario' | 'estado' | 'usuarioActualizacion' | 'fechaActualizacion'
>
