import * as XLSX from 'xlsx'
import { leerHoja } from '@/features/importacion/utils/leerHoja'
import { joinNombreCompleto } from '@/shared/utils/nombreCompuesto'
import type { CategoriaDetectada, CategoriaGrupo, FilaCargaGrupo } from '../types/grupo'
import { FILA_EJEMPLO_CARGA_GRUPO, HEADERS_CARGA_GRUPO } from '../constants/grupos.constants'
import { limpiarNombre, normalizarNombre } from './normalizar'

/** Descarga la plantilla de carga del grupo (se arma al vuelo; no hay archivo estático todavía). */
export function descargarPlantillaGrupo(nombreGrupo: string): void {
  const filas = [
    [`Carga de miembros · Grupo de interés: ${nombreGrupo}`],
    ['Una persona por fila. En CATEGORIA escriba la categoría dentro del grupo; si no existe, se crea al cargar. Puede dejarla vacía.'],
    [],
    HEADERS_CARGA_GRUPO,
    HEADERS_CARGA_GRUPO.map((h) => FILA_EJEMPLO_CARGA_GRUPO[h] ?? ''),
  ]
  const hoja = XLSX.utils.aoa_to_sheet(filas)
  hoja['!cols'] = HEADERS_CARGA_GRUPO.map(() => ({ wch: 18 }))
  const libro = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(libro, hoja, 'Datos')
  const slug = normalizarNombre(nombreGrupo).replace(/[^a-z0-9]+/g, '_') || 'grupo'
  XLSX.writeFile(libro, `Plantilla_Grupo_${slug}.xlsx`)
}

/** Lee el Excel y valida cada fila (documento y nombre son obligatorios). */
export async function leerArchivoGrupo(file: File): Promise<FilaCargaGrupo[]> {
  const filas = await leerHoja(file, HEADERS_CARGA_GRUPO, FILA_EJEMPLO_CARGA_GRUPO)
  const vistos = new Set<string>()
  return filas.map(({ filaExcel, valores: v }) => {
    const documento = (v['DOCUMENTO'] ?? '').replace(/[^\dA-Za-z]/g, '')
    const nombre = joinNombreCompleto({
      nombre1: v['PRIMER_NOMBRE'] ?? '', nombre2: v['SEGUNDO_NOMBRE'] ?? '',
      apellido1: v['PRIMER_APELLIDO'] ?? '', apellido2: v['SEGUNDO_APELLIDO'] ?? '',
    })
    let error: string | undefined
    if (!documento) error = 'Falta el documento.'
    else if (!v['PRIMER_NOMBRE'] || !v['PRIMER_APELLIDO']) error = 'Falta el primer nombre o el primer apellido.'
    else if (vistos.has(documento)) error = `El documento ${documento} está repetido en el archivo.`
    if (documento) vistos.add(documento)
    return {
      filaExcel, documento, nombre, error,
      tipoDocumento: (v['TIPO_DOCUMENTO'] ?? '').toUpperCase(),
      correo: v['CORREO'] ?? '', telefono: v['TELEFONO'] ?? '', ciudad: limpiarNombre((v['CIUDAD'] ?? '').toLowerCase()),
      categoria: v['CATEGORIA'] ?? '',
    }
  })
}

/**
 * Agrupa las categorías del archivo por nombre normalizado y las compara con las del grupo:
 * las que ya existen se asignan solas; las nuevas quedan marcadas para crearse (el usuario
 * puede renombrarlas o unirlas a una existente antes de confirmar).
 */
export function detectarCategorias(filas: FilaCargaGrupo[], existentes: CategoriaGrupo[]): CategoriaDetectada[] {
  const porClave = new Map<string, CategoriaDetectada>()
  for (const f of filas) {
    if (f.error) continue
    const clave = normalizarNombre(f.categoria)
    if (!clave) continue
    const actual = porClave.get(clave)
    const variante = f.categoria.trim()
    if (actual) {
      actual.filas++
      if (!actual.variantes.includes(variante)) actual.variantes.push(variante)
      continue
    }
    const existente = existentes.find((c) => normalizarNombre(c.nombre) === clave) ?? null
    porClave.set(clave, {
      clave, nombreArchivo: variante, variantes: [variante], filas: 1,
      existenteId: existente?.id ?? null,
      accion: existente ? 'unir' : 'crear',
      nombreFinal: existente ? existente.nombre : limpiarNombre(variante),
      unirConId: existente?.id ?? null,
    })
  }
  // Nuevas primero (son las que requieren revisión), luego por cantidad de filas.
  return [...porClave.values()].sort((a, b) => Number(!!a.existenteId) - Number(!!b.existenteId) || b.filas - a.filas)
}
