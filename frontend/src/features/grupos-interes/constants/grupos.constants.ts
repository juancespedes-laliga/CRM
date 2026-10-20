import type { CategoriaGrupo, GrupoDraft, GrupoInteres, MiembroGrupo } from '../types/grupo'

export const COLORES_GRUPO = ['#2447F9', '#EC4899', '#C9A227', '#059669', '#7C3AED', '#0EA5E9', '#F97316', '#1A2A6C']

export const GRUPO_DRAFT_VACIO: GrupoDraft = { nombre: '', descripcion: '', color: COLORES_GRUPO[0] }

// Plantilla de carga: mismas columnas de persona que la plantilla de contactos + CATEGORIA.
export const HEADERS_CARGA_GRUPO = [
  'PRIMER_NOMBRE', 'SEGUNDO_NOMBRE', 'PRIMER_APELLIDO', 'SEGUNDO_APELLIDO',
  'TIPO_DOCUMENTO', 'DOCUMENTO', 'CORREO', 'TELEFONO', 'CIUDAD', 'CATEGORIA',
]
export const FILA_EJEMPLO_CARGA_GRUPO: Record<string, string> = {
  PRIMER_NOMBRE: 'JUAN', SEGUNDO_NOMBRE: 'CARLOS', PRIMER_APELLIDO: 'GOMEZ', SEGUNDO_APELLIDO: 'RESTREPO',
  TIPO_DOCUMENTO: 'CC', DOCUMENTO: '1088123456', CORREO: 'juan.gomez@correo.com', TELEFONO: '3101234567',
  CIUDAD: 'PEREIRA', CATEGORIA: 'Recurrente',
}

// ── Datos de ejemplo (mientras no exista el backend) ─────────────────────
export const GRUPOS_MOCK: GrupoInteres[] = [
  { id: 1, nombre: 'Donantes', descripcion: 'Personas que apoyan económicamente a la Fundación.', color: '#EC4899', activo: true, totalMiembros: 0, fechaCreacion: '2026-08-12' },
  { id: 2, nombre: 'Voluntarios', descripcion: 'Personas que participan en jornadas y eventos.', color: '#059669', activo: true, totalMiembros: 0, fechaCreacion: '2026-09-01' },
  { id: 3, nombre: 'Aliados', descripcion: 'Empresas, entidades públicas y medios con los que hay convenio.', color: '#2447F9', activo: true, totalMiembros: 0, fechaCreacion: '2026-09-20' },
]

export const CATEGORIAS_MOCK: CategoriaGrupo[] = [
  { id: 1, grupoId: 1, nombre: 'Recurrente', totalMiembros: 0 },
  { id: 2, grupoId: 1, nombre: 'Ocasional', totalMiembros: 0 },
  { id: 3, grupoId: 1, nombre: 'Corporativo', totalMiembros: 0 },
  { id: 4, grupoId: 2, nombre: 'Jornadas de salud', totalMiembros: 0 },
  { id: 5, grupoId: 2, nombre: 'Eventos', totalMiembros: 0 },
  { id: 6, grupoId: 3, nombre: 'Empresas', totalMiembros: 0 },
  { id: 7, grupoId: 3, nombre: 'Gobierno', totalMiembros: 0 },
  { id: 8, grupoId: 3, nombre: 'Medios', totalMiembros: 0 },
]

const m = (id: number, grupoId: number, documento: string, nombre: string, categoriaId: number | null, ciudad = 'Pereira'): MiembroGrupo => ({
  id, grupoId, contactoId: id, tipoDocumento: 'CC', documento, nombre,
  correo: nombre.split(' ')[0].toLowerCase() + '@ejemplo.com', telefono: '300 000 ' + String(1000 + id).slice(-4),
  ciudad, categoriaId, fechaIngreso: '2026-09-' + String(10 + (id % 18)).padStart(2, '0'),
})

export const MIEMBROS_MOCK: MiembroGrupo[] = [
  m(1, 1, '42100001', 'Diana Ríos Salazar', 1),
  m(2, 1, '10200002', 'Álvaro Nieto Mejía', 1, 'Dosquebradas'),
  m(3, 1, '42100003', 'Yenifer Tunubalá Castro', 2),
  m(4, 1, '42100004', 'Carolina Muñoz Pérez', 3, 'Santa Rosa de Cabal'),
  m(5, 1, '10200005', 'Gustavo Marín Ruiz', 2, 'Manizales'),
  m(6, 1, '42100006', 'Omaira Salazar Vélez', null),
  m(7, 2, '10200007', 'Fernando Arias Gómez', 4),
  m(8, 2, '42100008', 'Luz Marina Ospina', 5),
  m(9, 2, '42100009', 'Patricia Vargas Ruiz', 4, 'Dosquebradas'),
  m(10, 3, '10200010', 'Ricardo Mejía Torres', 6),
  m(11, 3, '42100011', 'Natalia Cárdenas López', 7),
]
