import { computed, reactive, ref, watch, type Ref } from 'vue'
import { getCambios, LIMITE_CAMBIOS, type ConsultaCambios, type ResumenCambios } from '../services/auditoria.api'
import { accionesDeModulo, incluyePlanLiga, modulosDeVista } from '../constants/auditoria.constants'
import type { FiltrosCambios, ModuloSeleccion, RegistroCambio, UsuarioAuditoria } from '../types/auditoria'

/** Filas por página del registro de cambios. */
export const POR_PAGINA_CAMBIOS = 20

/** Espera al escribir en el buscador antes de consultar (ms). */
const ESPERA_BUSQUEDA = 350

const filtrosVacios = (): FiltrosCambios => ({
  buscar: '',
  submodulo: 'todos',
  accion: 'todas',
  usuario: 'todos',
  origen: 'todos',
  estado: 'todos',
  renovado: 'todos',
  desde: '',
  hasta: '',
})

const resumenVacio = (): ResumenCambios => ({ total: 0, usuarios: 0, cambiosEstado: 0, renovaciones: 0, masivos: 0 })

/**
 * Registro de cambios acotado al módulo seleccionado, paginado en el servidor:
 * la búsqueda (cédula, nombre, ID, usuario), los filtros y los totales de las
 * tarjetas los resuelve el backend sobre toda la tabla; aquí solo llega la página.
 */
export function useCambiosAuditoria(modulo: Ref<ModuloSeleccion>) {
  const cambios = ref<RegistroCambio[]>([])
  const total = ref(0)
  const resumen = ref<ResumenCambios>(resumenVacio())
  const usuarios = ref<UsuarioAuditoria[]>([])
  const estados = ref<string[]>([])
  const cargando = ref(false)
  const error = ref<string | null>(null)

  const filtros = reactive<FiltrosCambios>(filtrosVacios())
  const pagina = ref(1)

  const accionesDisponibles = computed(() => accionesDeModulo(modulo.value))
  const muestraPlanLiga = computed(() => incluyePlanLiga(modulo.value))
  /** Módulos que abarca la vista; si son varios se puede filtrar por uno y se muestra la columna Módulo. */
  const submodulosDisponibles = computed(() => modulosDeVista(modulo.value))
  const variosModulos = computed(() => submodulosDisponibles.value.length > 1)

  /** Filtros actuales traducidos a la consulta del API (sin página). */
  function consulta(): ConsultaCambios {
    return {
      desde: filtros.desde || undefined,
      hasta: filtros.hasta || undefined,
      submodulo: filtros.submodulo === 'todos' ? undefined : filtros.submodulo,
      buscar: filtros.buscar.trim() || undefined,
      accion: filtros.accion === 'todas' ? undefined : filtros.accion,
      usuario: filtros.usuario === 'todos' ? undefined : filtros.usuario,
      origen: filtros.origen === 'todos' ? undefined : filtros.origen,
      estado: filtros.estado === 'todos' ? undefined : filtros.estado,
      renovado: filtros.renovado === 'todos' ? undefined : filtros.renovado === 'si',
    }
  }

  let peticion = 0
  async function cargar() {
    const id = ++peticion
    cargando.value = true
    error.value = null
    try {
      const data = await getCambios(modulo.value, { ...consulta(), pagina: pagina.value, porPagina: POR_PAGINA_CAMBIOS })
      if (id !== peticion) return
      cambios.value = data.items
      total.value = data.total
      resumen.value = data.resumen
      usuarios.value = data.usuarios
      estados.value = data.estados
      // Si la página quedó fuera de rango (p. ej. tras borrar registros), vuelve a la última.
      const ultima = Math.max(1, Math.ceil(data.total / POR_PAGINA_CAMBIOS))
      if (pagina.value > ultima) pagina.value = ultima
    } catch (e) {
      if (id === peticion) error.value = e instanceof Error ? e.message : 'No se pudo cargar el registro de cambios.'
    } finally {
      if (id === peticion) cargando.value = false
    }
  }

  /** Todos los cambios que cumplen los filtros (para exportar), hasta el tope del backend. */
  async function cargarTodos(): Promise<{ items: RegistroCambio[]; truncado: boolean }> {
    const data = await getCambios(modulo.value, { ...consulta(), pagina: 1, porPagina: LIMITE_CAMBIOS })
    return { items: data.items, truncado: data.truncado }
  }

  /** Vuelve a la página 1 y consulta; si ya estaba en la 1, el watch de página no dispara. */
  function recargarDesdeInicio() {
    if (pagina.value !== 1) pagina.value = 1
    else cargar()
  }

  // Al cambiar de módulo: se limpian filtros que ya no aplican y se recarga.
  watch(modulo, () => {
    if (filtros.accion !== 'todas' && !accionesDisponibles.value.includes(filtros.accion)) filtros.accion = 'todas'
    if (!muestraPlanLiga.value) filtros.renovado = 'todos'
    filtros.usuario = 'todos'
    filtros.estado = 'todos'
    filtros.submodulo = 'todos'
    recargarDesdeInicio()
  })

  watch(pagina, () => cargar())

  // Filtros de lista y fechas: consulta inmediata.
  watch(
    () => [filtros.submodulo, filtros.accion, filtros.usuario, filtros.origen, filtros.estado, filtros.renovado, filtros.desde, filtros.hasta],
    () => recargarDesdeInicio(),
  )

  // Buscador: espera a que se deje de escribir.
  let temporizador: ReturnType<typeof setTimeout> | undefined
  watch(() => filtros.buscar, () => {
    clearTimeout(temporizador)
    temporizador = setTimeout(recargarDesdeInicio, ESPERA_BUSQUEDA)
  })

  const hayFiltros = computed(() => {
    const v = filtrosVacios()
    return (Object.keys(v) as (keyof FiltrosCambios)[]).some(k => filtros[k] !== v[k])
  })

  function limpiarFiltros() {
    Object.assign(filtros, filtrosVacios())
  }

  return {
    cambios, total, cargando, error, cargar, cargarTodos,
    filtros, limpiarFiltros, hayFiltros,
    accionesDisponibles, muestraPlanLiga, submodulosDisponibles, variosModulos,
    usuarios, estados,
    pagina,
    resumen,
  }
}
