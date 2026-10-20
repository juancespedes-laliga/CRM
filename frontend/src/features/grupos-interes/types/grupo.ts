export interface GrupoInteres {
  id: number
  nombre: string
  descripcion: string
  color: string
  activo: boolean
  totalMiembros: number
  fechaCreacion: string
}

export interface GrupoDraft {
  nombre: string
  descripcion: string
  color: string
}

export interface CategoriaGrupo {
  id: number
  grupoId: number
  nombre: string
  totalMiembros: number
}

export interface MiembroGrupo {
  id: number
  grupoId: number
  /** Contacto del CRM al que corresponde (se busca/crea por documento). */
  contactoId: number
  tipoDocumento: string
  documento: string
  nombre: string
  correo: string
  telefono: string
  ciudad: string
  /** null = miembro sin categoría dentro del grupo. */
  categoriaId: number | null
  fechaIngreso: string
}

/** Una fila del Excel ya interpretada, antes de guardarse. */
export interface FilaCargaGrupo {
  filaExcel: number
  tipoDocumento: string
  documento: string
  nombre: string
  correo: string
  telefono: string
  ciudad: string
  /** Texto tal como vino en la columna CATEGORIA. */
  categoria: string
  error?: string
}

/** Categoría distinta encontrada en el archivo, con lo que se hará con ella al confirmar. */
export interface CategoriaDetectada {
  /** Clave normalizada (sin tildes, minúsculas, espacios simples). */
  clave: string
  /** Nombre como aparece en el archivo (la primera variante encontrada). */
  nombreArchivo: string
  /** Variantes distintas del mismo nombre en el archivo (ej. "Recurrente" / "recurrente "). */
  variantes: string[]
  filas: number
  /** Si ya existe en el grupo, su id. */
  existenteId: number | null
  /** 'crear' = categoría nueva; 'unir' = asignar a una existente (unirConId). */
  accion: 'crear' | 'unir'
  nombreFinal: string
  unirConId: number | null
}

export interface ResultadoCargaGrupo {
  filas: number
  agregados: number
  yaEranMiembros: number
  contactosNuevos: number
  categoriasCreadas: string[]
  errores: { filaExcel: number; mensaje: string }[]
}

/** Persona a agregar a un grupo desde otra vista (ej. las seleccionadas en Audiencias). */
export interface PersonaParaGrupo {
  documento: string
  nombre: string
  correo: string | null
  telefono: string | null
  ciudad: string
}
