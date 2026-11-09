import { computed, reactive, ref, watch } from 'vue'
import { getRenovaciones } from '../services/auditoria.api'
import { POR_PAGINA } from '../constants/auditoria.constants'
import { diasHasta, vigenciaDe } from '../utils/fechas'
import type { FiltrosRenovaciones, RenovacionRegistro } from '../types/auditoria'

const filtrosVacios = (): FiltrosRenovaciones => ({
  buscar: '',
  tipo: 'todos',
  renovado: 'todos',
  vigencia: 'todas',
  estado: 'todos',
})

const normalizar = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

/** Renovaciones de Plan Liga (titulares y beneficiarios). */
export function useRenovacionesAuditoria() {
  const registros = ref<RenovacionRegistro[]>([])
  const cargando = ref(false)
  const error = ref<string | null>(null)
  const filtros = reactive<FiltrosRenovaciones>(filtrosVacios())
  const pagina = ref(1)

  async function cargar() {
    cargando.value = true
    error.value = null
    try {
      registros.value = await getRenovaciones()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'No se pudo cargar el listado de renovaciones.'
    } finally {
      cargando.value = false
    }
  }

  const delTipo = computed(() =>
    filtros.tipo === 'todos' ? registros.value : registros.value.filter(r => r.tipo === filtros.tipo),
  )

  const estados = computed(() => [...new Set(delTipo.value.map(r => r.estado))].sort())

  /** Filtrado sin aplicar el filtro de vigencia/renovado: base para las tarjetas. */
  const baseTarjetas = computed(() => {
    const q = normalizar(filtros.buscar.trim())
    return delTipo.value.filter(r => {
      if (filtros.estado !== 'todos' && r.estado !== filtros.estado) return false
      if (q) {
        // Igual que en Titulares y Beneficiarios: por cédula, nombre o empresa
        // (también encuentra por plan, tipo de plan —ej. 'CYP'— y por el titular del grupo).
        const texto = normalizar([r.documento, r.nombre, r.empresa, String(r.id), r.plan, r.tipoPlan, r.titular?.nombre ?? ''].join(' '))
        if (!texto.includes(q)) return false
      }
      return true
    })
  })

  const filtrados = computed(() =>
    baseTarjetas.value
      .filter(r => {
        if (filtros.renovado === 'si' && !r.renovado) return false
        if (filtros.renovado === 'no' && r.renovado) return false
        if (filtros.vigencia !== 'todas' && vigenciaDe(r.vencimiento) !== filtros.vigencia) return false
        return true
      })
      // Primero lo que está más cerca de vencer (los vencidos más recientes van antes que los viejos).
      .sort((a, b) => Math.abs(diasHasta(a.vencimiento)) - Math.abs(diasHasta(b.vencimiento))),
  )

  const resumen = computed(() => {
    const base = baseTarjetas.value
    return {
      renovados: base.filter(r => r.renovado).length,
      sinRenovar: base.filter(r => !r.renovado).length,
      porVencer: base.filter(r => vigenciaDe(r.vencimiento) === 'por_vencer').length,
      vencidos: base.filter(r => vigenciaDe(r.vencimiento) === 'vencido').length,
    }
  })

  type Tarjeta = 'renovados' | 'sinRenovar' | 'porVencer' | 'vencidos'
  const tarjetaActiva = computed<Tarjeta | null>(() => {
    if (filtros.renovado === 'si' && filtros.vigencia === 'todas') return 'renovados'
    if (filtros.renovado === 'no' && filtros.vigencia === 'todas') return 'sinRenovar'
    if (filtros.vigencia === 'por_vencer' && filtros.renovado === 'todos') return 'porVencer'
    if (filtros.vigencia === 'vencido' && filtros.renovado === 'todos') return 'vencidos'
    return null
  })

  /** Clic en una tarjeta: filtra la tabla; otro clic en la misma quita el filtro. */
  function filtrarPorTarjeta(t: Tarjeta) {
    const yaActiva = tarjetaActiva.value === t
    filtros.renovado = 'todos'
    filtros.vigencia = 'todas'
    if (yaActiva) return
    if (t === 'renovados') filtros.renovado = 'si'
    if (t === 'sinRenovar') filtros.renovado = 'no'
    if (t === 'porVencer') filtros.vigencia = 'por_vencer'
    if (t === 'vencidos') filtros.vigencia = 'vencido'
  }

  watch(() => ({ ...filtros }), () => { pagina.value = 1 })

  const paginados = computed(() => filtrados.value.slice((pagina.value - 1) * POR_PAGINA, pagina.value * POR_PAGINA))

  const hayFiltros = computed(() => {
    const v = filtrosVacios()
    return (Object.keys(v) as (keyof FiltrosRenovaciones)[]).some(k => filtros[k] !== v[k])
  })

  function limpiarFiltros() {
    Object.assign(filtros, filtrosVacios())
  }

  return {
    registros, cargando, error, cargar,
    filtros, limpiarFiltros, hayFiltros,
    estados,
    filtrados, paginados, pagina,
    resumen, tarjetaActiva, filtrarPorTarjeta,
  }
}
