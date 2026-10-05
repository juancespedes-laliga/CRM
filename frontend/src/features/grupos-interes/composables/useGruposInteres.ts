import { computed, ref } from 'vue'
import type { CategoriaGrupo, GrupoDraft, GrupoInteres, MiembroGrupo } from '../types/grupo'
import * as api from '../services/grupos.api'
import { normalizarNombre } from '../utils/normalizar'

/** 'todas' | 'sin' (sin categoría) | id de categoría */
export type FiltroCategoria = 'todas' | 'sin' | number
/** Filtro por datos de contacto de los miembros. */
export type FiltroContacto = 'todos' | 'con_correo' | 'con_celular' | 'sin_correo'

export function useGruposInteres() {
  const grupos = ref<GrupoInteres[]>([])
  const cargandoGrupos = ref(false)
  const grupoId = ref<number | null>(null)
  const grupo = computed(() => grupos.value.find((g) => g.id === grupoId.value) ?? null)

  const categorias = ref<CategoriaGrupo[]>([])
  const miembros = ref<MiembroGrupo[]>([])
  const cargandoDetalle = ref(false)
  const error = ref<string | null>(null)

  const buscar = ref('')
  const filtroCategoria = ref<FiltroCategoria>('todas')
  const filtroCiudad = ref('todas')
  const filtroContacto = ref<FiltroContacto>('todos')
  const ciudades = computed(() => [...new Set(miembros.value.map((mi) => mi.ciudad).filter(Boolean))].sort())
  const filtrosMiembrosActivos = computed(() =>
    Number(!!buscar.value.trim()) + Number(filtroCiudad.value !== 'todas') + Number(filtroContacto.value !== 'todos'))
  const limpiarFiltrosMiembros = () => { buscar.value = ''; filtroCiudad.value = 'todas'; filtroContacto.value = 'todos' }

  const miembrosFiltrados = computed(() => {
    const q = normalizarNombre(buscar.value)
    return miembros.value.filter((mi) => {
      if (filtroCategoria.value === 'sin' && mi.categoriaId !== null) return false
      if (typeof filtroCategoria.value === 'number' && mi.categoriaId !== filtroCategoria.value) return false
      if (filtroCiudad.value !== 'todas' && mi.ciudad !== filtroCiudad.value) return false
      if (filtroContacto.value === 'con_correo' && !mi.correo) return false
      if (filtroContacto.value === 'con_celular' && !mi.telefono) return false
      if (filtroContacto.value === 'sin_correo' && mi.correo) return false
      if (!q) return true
      return [mi.nombre, mi.documento, mi.correo, mi.ciudad].some((v) => normalizarNombre(v).includes(q))
    })
  })
  const sinCategoria = computed(() => miembros.value.filter((mi) => mi.categoriaId === null).length)

  const ejecutar = async (accion: () => Promise<unknown>): Promise<boolean> => {
    error.value = null
    try { await accion(); return true } catch (e) {
      error.value = e instanceof Error ? e.message : 'Ocurrió un error inesperado.'
      return false
    }
  }

  const cargarGrupos = async () => {
    cargandoGrupos.value = true
    await ejecutar(async () => { grupos.value = await api.getGrupos() })
    cargandoGrupos.value = false
    if (grupoId.value === null && grupos.value.length) await seleccionar(grupos.value[0].id)
  }

  const cargarDetalle = async () => {
    if (grupoId.value === null) return
    const id = grupoId.value
    cargandoDetalle.value = true
    await ejecutar(async () => {
      const [cats, mis] = await Promise.all([api.getCategorias(id), api.getMiembros(id)])
      categorias.value = cats
      miembros.value = mis
    })
    cargandoDetalle.value = false
  }

  const refrescar = async () => {
    await ejecutar(async () => { grupos.value = await api.getGrupos() })
    await cargarDetalle()
  }

  const seleccionar = async (id: number) => {
    grupoId.value = id
    filtroCategoria.value = 'todas'
    limpiarFiltrosMiembros()
    await cargarDetalle()
  }

  const crearGrupo = (data: GrupoDraft) => ejecutar(async () => {
    const nuevo = await api.crearGrupo(data)
    grupos.value = await api.getGrupos()
    await seleccionar(nuevo.id)
  })
  const actualizarGrupo = (id: number, data: GrupoDraft) => ejecutar(async () => {
    await api.actualizarGrupo(id, data)
    grupos.value = await api.getGrupos()
  })
  const eliminarGrupo = (id: number) => ejecutar(async () => {
    await api.eliminarGrupo(id)
    grupos.value = await api.getGrupos()
    grupoId.value = null
    categorias.value = []
    miembros.value = []
    if (grupos.value.length) await seleccionar(grupos.value[0].id)
  })

  const crearCategoria = (nombre: string) => ejecutar(async () => {
    if (grupoId.value === null) return
    await api.crearCategoria(grupoId.value, nombre)
    await cargarDetalle()
  })
  const renombrarCategoria = (id: number, nombre: string) => ejecutar(async () => {
    await api.renombrarCategoria(id, nombre)
    await cargarDetalle()
  })
  const eliminarCategoria = (id: number) => ejecutar(async () => {
    await api.eliminarCategoria(id)
    if (filtroCategoria.value === id) filtroCategoria.value = 'todas'
    await cargarDetalle()
  })

  const cambiarCategoriaMiembro = (miembroId: number, categoriaId: number | null) => ejecutar(async () => {
    await api.cambiarCategoriaMiembro(miembroId, categoriaId)
    await cargarDetalle()
  })
  const quitarMiembro = (miembroId: number) => ejecutar(async () => {
    await api.quitarMiembro(miembroId)
    await refrescar()
  })

  return {
    grupos, cargandoGrupos, grupoId, grupo, categorias, miembros, cargandoDetalle, error,
    buscar, filtroCategoria, filtroCiudad, filtroContacto, ciudades, filtrosMiembrosActivos, limpiarFiltrosMiembros,
    miembrosFiltrados, sinCategoria,
    cargarGrupos, seleccionar, refrescar,
    crearGrupo, actualizarGrupo, eliminarGrupo,
    crearCategoria, renombrarCategoria, eliminarCategoria,
    cambiarCategoriaMiembro, quitarMiembro,
  }
}
