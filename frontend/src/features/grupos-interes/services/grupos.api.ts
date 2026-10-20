// Servicio de grupos de interés. TODAVÍA NO HAY BACKEND: los datos viven en memoria (se
// reinician al recargar la página) para poder ver y ajustar el flujo. Cada función indica el
// endpoint que la reemplazará; la firma (parámetros y retorno) ya es la definitiva, así que al
// conectar el backend solo cambia el cuerpo de cada una.
import type {
  CategoriaGrupo, FilaCargaGrupo, GrupoDraft, GrupoInteres, MiembroGrupo, ResultadoCargaGrupo,
} from '../types/grupo'
import { CATEGORIAS_MOCK, GRUPOS_MOCK, MIEMBROS_MOCK } from '../constants/grupos.constants'
import { limpiarNombre, normalizarNombre } from '../utils/normalizar'

let grupos = GRUPOS_MOCK.map((g) => ({ ...g }))
let categorias = CATEGORIAS_MOCK.map((c) => ({ ...c }))
let miembros = MIEMBROS_MOCK.map((mi) => ({ ...mi }))
let siguienteId = 1000
const nuevoId = () => ++siguienteId
const hoy = () => new Date().toISOString().split('T')[0]
const pausa = () => new Promise((r) => setTimeout(r, 150))

// GET /api/grupos-interes
export async function getGrupos(): Promise<GrupoInteres[]> {
  await pausa()
  return grupos.map((g) => ({ ...g, totalMiembros: miembros.filter((mi) => mi.grupoId === g.id).length }))
}

// POST /api/grupos-interes
export async function crearGrupo(data: GrupoDraft): Promise<GrupoInteres> {
  await pausa()
  const nombre = limpiarNombre(data.nombre)
  if (grupos.some((g) => normalizarNombre(g.nombre) === normalizarNombre(nombre))) {
    throw new Error(`Ya existe un grupo llamado "${nombre}".`)
  }
  const nuevo: GrupoInteres = { id: nuevoId(), nombre, descripcion: data.descripcion.trim(), color: data.color, activo: true, totalMiembros: 0, fechaCreacion: hoy() }
  grupos = [...grupos, nuevo]
  return nuevo
}

// PUT /api/grupos-interes/{id}
export async function actualizarGrupo(id: number, data: GrupoDraft): Promise<void> {
  await pausa()
  const nombre = limpiarNombre(data.nombre)
  if (grupos.some((g) => g.id !== id && normalizarNombre(g.nombre) === normalizarNombre(nombre))) {
    throw new Error(`Ya existe un grupo llamado "${nombre}".`)
  }
  grupos = grupos.map((g) => (g.id === id ? { ...g, nombre, descripcion: data.descripcion.trim(), color: data.color } : g))
}

// DELETE /api/grupos-interes/{id}
export async function eliminarGrupo(id: number): Promise<void> {
  await pausa()
  grupos = grupos.filter((g) => g.id !== id)
  categorias = categorias.filter((c) => c.grupoId !== id)
  miembros = miembros.filter((mi) => mi.grupoId !== id)
}

// GET /api/grupos-interes/{id}/categorias
export async function getCategorias(grupoId: number): Promise<CategoriaGrupo[]> {
  await pausa()
  return categorias
    .filter((c) => c.grupoId === grupoId)
    .map((c) => ({ ...c, totalMiembros: miembros.filter((mi) => mi.categoriaId === c.id).length }))
}

// POST /api/grupos-interes/{id}/categorias
export async function crearCategoria(grupoId: number, nombre: string): Promise<CategoriaGrupo> {
  await pausa()
  const limpio = limpiarNombre(nombre)
  if (!limpio) throw new Error('Escriba el nombre de la categoría.')
  if (categorias.some((c) => c.grupoId === grupoId && normalizarNombre(c.nombre) === normalizarNombre(limpio))) {
    throw new Error(`La categoría "${limpio}" ya existe en este grupo.`)
  }
  const nueva: CategoriaGrupo = { id: nuevoId(), grupoId, nombre: limpio, totalMiembros: 0 }
  categorias = [...categorias, nueva]
  return nueva
}

// PUT /api/grupos-interes/categorias/{id}
export async function renombrarCategoria(id: number, nombre: string): Promise<void> {
  await pausa()
  const actual = categorias.find((c) => c.id === id)
  if (!actual) return
  const limpio = limpiarNombre(nombre)
  if (!limpio) throw new Error('Escriba el nombre de la categoría.')
  if (categorias.some((c) => c.id !== id && c.grupoId === actual.grupoId && normalizarNombre(c.nombre) === normalizarNombre(limpio))) {
    throw new Error(`La categoría "${limpio}" ya existe en este grupo.`)
  }
  categorias = categorias.map((c) => (c.id === id ? { ...c, nombre: limpio } : c))
}

// DELETE /api/grupos-interes/categorias/{id}  (sus miembros quedan "Sin categoría")
export async function eliminarCategoria(id: number): Promise<void> {
  await pausa()
  categorias = categorias.filter((c) => c.id !== id)
  miembros = miembros.map((mi) => (mi.categoriaId === id ? { ...mi, categoriaId: null } : mi))
}

// GET /api/grupos-interes/{id}/miembros
export async function getMiembros(grupoId: number): Promise<MiembroGrupo[]> {
  await pausa()
  return miembros.filter((mi) => mi.grupoId === grupoId).map((mi) => ({ ...mi }))
}

// PATCH /api/grupos-interes/miembros/{id}
export async function cambiarCategoriaMiembro(miembroId: number, categoriaId: number | null): Promise<void> {
  await pausa()
  miembros = miembros.map((mi) => (mi.id === miembroId ? { ...mi, categoriaId } : mi))
}

// DELETE /api/grupos-interes/miembros/{id}  (quita a la persona del grupo; el contacto sigue en el CRM)
export async function quitarMiembro(miembroId: number): Promise<void> {
  await pausa()
  miembros = miembros.filter((mi) => mi.id !== miembroId)
}

// POST /api/grupos-interes/{id}/categorias/lote
// Crea solo las que no existen (comparando por nombre normalizado) y devuelve
// nombre normalizado -> id de TODAS las pedidas.
export async function crearCategoriasLote(grupoId: number, nombres: string[]): Promise<{ ids: Record<string, number>; creadas: string[] }> {
  await pausa()
  const ids: Record<string, number> = {}
  const creadas: string[] = []
  for (const nombre of nombres) {
    const clave = normalizarNombre(nombre)
    if (!clave || ids[clave]) continue
    const existente = categorias.find((c) => c.grupoId === grupoId && normalizarNombre(c.nombre) === clave)
    if (existente) { ids[clave] = existente.id; continue }
    const nueva: CategoriaGrupo = { id: nuevoId(), grupoId, nombre: limpiarNombre(nombre), totalMiembros: 0 }
    categorias = [...categorias, nueva]
    ids[clave] = nueva.id
    creadas.push(nueva.nombre)
  }
  return { ids, creadas }
}

// POST /api/grupos-interes/{id}/miembros/lote
// El backend busca cada persona por documento en mercadeo_crm_contactos (la crea si no existe)
// y la vincula al grupo con su categoría. Si ya era miembro, solo actualiza la categoría.
export async function agregarMiembrosLote(
  grupoId: number,
  filas: (FilaCargaGrupo & { categoriaId: number | null })[],
): Promise<Omit<ResultadoCargaGrupo, 'categoriasCreadas'>> {
  await pausa()
  let agregados = 0, yaEranMiembros = 0, contactosNuevos = 0
  const errores: ResultadoCargaGrupo['errores'] = []
  const documentosCRM = new Set(MIEMBROS_MOCK.map((mi) => mi.documento))
  for (const f of filas) {
    if (f.error) { errores.push({ filaExcel: f.filaExcel, mensaje: f.error }); continue }
    const existente = miembros.find((mi) => mi.grupoId === grupoId && mi.documento === f.documento)
    if (existente) {
      miembros = miembros.map((mi) => (mi.id === existente.id ? { ...mi, categoriaId: f.categoriaId } : mi))
      yaEranMiembros++
      continue
    }
    if (!documentosCRM.has(f.documento)) contactosNuevos++
    miembros = [...miembros, {
      id: nuevoId(), grupoId, contactoId: nuevoId(), tipoDocumento: f.tipoDocumento || 'CC', documento: f.documento,
      nombre: f.nombre, correo: f.correo, telefono: f.telefono, ciudad: f.ciudad, categoriaId: f.categoriaId, fechaIngreso: hoy(),
    }]
    agregados++
  }
  return { filas: filas.length, agregados, yaEranMiembros, contactosNuevos, errores }
}
