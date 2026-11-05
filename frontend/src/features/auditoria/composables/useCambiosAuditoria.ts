import { computed, reactive, ref, watch, type Ref } from 'vue'
import { getCambios } from '../services/auditoria.api'
import {
  ACCION_LABEL, MODULO_POR_KEY, ORIGEN_LABEL, POR_PAGINA, accionesDeModulo, esOrigenMasivo, incluyePlanLiga, modulosDeVista,
} from '../constants/auditoria.constants'
import type { FiltrosCambios, ModuloSeleccion, RegistroCambio, UsuarioAuditoria } from '../types/auditoria'

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

const normalizar = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

/**
 * Registro de cambios acotado al módulo seleccionado. Al cambiar de módulo se
 * recarga desde el API y se limpian los filtros que no aplican a ese módulo
 * (p. ej. "Renovado" fuera de Plan Liga, o una acción que el módulo no tiene).
 */
export function useCambiosAuditoria(modulo: Ref<ModuloSeleccion>) {
  const cambios = ref<RegistroCambio[]>([])
  const truncado = ref(false)
  const cargando = ref(false)
  const error = ref<string | null>(null)

  const filtros = reactive<FiltrosCambios>(filtrosVacios())
  const pagina = ref(1)

  let peticion = 0
  async function cargar() {
    const id = ++peticion
    cargando.value = true
    error.value = null
    try {
      const data = await getCambios(modulo.value, { desde: filtros.desde, hasta: filtros.hasta })
      if (id === peticion) {
        cambios.value = data.items
        truncado.value = data.truncado
      }
    } catch (e) {
      if (id === peticion) error.value = e instanceof Error ? e.message : 'No se pudo cargar el registro de cambios.'
    } finally {
      if (id === peticion) cargando.value = false
    }
  }

  const accionesDisponibles = computed(() => accionesDeModulo(modulo.value))
  const muestraPlanLiga = computed(() => incluyePlanLiga(modulo.value))
  /** Módulos que abarca la vista; si son varios se puede filtrar por uno y se muestra la columna Módulo. */
  const submodulosDisponibles = computed(() => modulosDeVista(modulo.value))
  const variosModulos = computed(() => submodulosDisponibles.value.length > 1)

  // Al cambiar de módulo: se limpian filtros que ya no aplican y se recarga.
  watch(modulo, () => {
    if (filtros.accion !== 'todas' && !accionesDisponibles.value.includes(filtros.accion)) filtros.accion = 'todas'
    if (!muestraPlanLiga.value) filtros.renovado = 'todos'
    filtros.usuario = 'todos'
    filtros.estado = 'todos'
    pagina.value = 1
    cargar()
  })

  // El rango de fechas se consulta en el servidor; el resto se filtra aquí.
  watch(() => [filtros.desde, filtros.hasta], () => {
    pagina.value = 1
    cargar()
  })

  const usuarios = computed<UsuarioAuditoria[]>(() => {
    const map = new Map<number, UsuarioAuditoria>()
    for (const c of cambios.value) map.set(c.usuario.id, c.usuario)
    return [...map.values()].sort((a, b) => a.nombre.localeCompare(b.nombre))
  })

  const estados = computed(() => {
    const set = new Set<string>()
    for (const c of cambios.value) if (c.estadoDespues) set.add(c.estadoDespues)
    return [...set].sort()
  })

  const filtrados = computed(() => {
    const q = normalizar(filtros.buscar.trim())
    return cambios.value.filter(c => {
      if (filtros.submodulo !== 'todos' && c.modulo !== filtros.submodulo) return false
      if (filtros.accion !== 'todas' && c.accion !== filtros.accion) return false
      if (filtros.usuario !== 'todos' && c.usuario.id !== filtros.usuario) return false
      if (filtros.origen !== 'todos' && c.origen !== filtros.origen) return false
      if (filtros.estado !== 'todos' && c.estadoDespues !== filtros.estado) return false
      if (filtros.renovado === 'si' && c.renovado !== true) return false
      if (filtros.renovado === 'no' && c.renovado !== false) return false
      if (q) {
        const texto = normalizar([
          c.registroNombre, c.documento, String(c.registroId), c.usuario.nombre, c.usuario.usuario,
          c.motivo, ACCION_LABEL[c.accion], ORIGEN_LABEL[c.origen], MODULO_POR_KEY[c.modulo].label,
          c.grupoTitular?.nombre ?? '', c.grupoTitular?.documento ?? '',
        ].join(' '))
        if (!texto.includes(q)) return false
      }
      return true
    })
  })

  watch(() => [filtros.buscar, filtros.submodulo, filtros.accion, filtros.usuario, filtros.origen, filtros.estado, filtros.renovado], () => {
    pagina.value = 1
  })

  const paginados = computed(() => filtrados.value.slice((pagina.value - 1) * POR_PAGINA, pagina.value * POR_PAGINA))

  const resumen = computed(() => {
    const lista = filtrados.value
    return {
      total: lista.length,
      usuarios: new Set(lista.map(c => c.usuario.id)).size,
      cambiosEstado: lista.filter(c => c.estadoAntes !== null && c.estadoAntes !== c.estadoDespues).length,
      renovaciones: lista.filter(c => c.accion === 'renovacion').length,
      masivos: lista.filter(c => esOrigenMasivo(c.origen)).length,
    }
  })

  const hayFiltros = computed(() => {
    const v = filtrosVacios()
    return (Object.keys(v) as (keyof FiltrosCambios)[]).some(k => filtros[k] !== v[k])
  })

  function limpiarFiltros() {
    Object.assign(filtros, filtrosVacios())
  }

  return {
    cambios, truncado, cargando, error, cargar,
    filtros, limpiarFiltros, hayFiltros,
    accionesDisponibles, muestraPlanLiga, submodulosDisponibles, variosModulos,
    usuarios, estados,
    filtrados, paginados, pagina,
    resumen,
  }
}
