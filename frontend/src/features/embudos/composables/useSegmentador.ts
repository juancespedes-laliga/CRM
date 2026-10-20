import { computed, reactive, ref } from 'vue'
import {
  clonarFiltro, contarFiltros, filtroVacio,
  type FiltroSegmento,
} from '../constants/ciclo-afiliado.constants'
import { getBloqueAudiencia, TAMANO_BLOQUE, type PersonaAudiencia } from '../services/segmentos.api'

export const POR_PAGINA = 10

const f = reactive<FiltroSegmento>(filtroVacio())
const fApp = ref<FiltroSegmento>(filtroVacio())
// Se carga de a bloques (ver TAMANO_BLOQUE en segmentos.api.ts), no toda la
// audiencia de una vez: solo se pide el bloque que el usuario esta viendo.
// Si avanza mas alla, ahi se pide el siguiente bloque (no todo de entrada).
const bloques = ref<Map<number, PersonaAudiencia[]>>(new Map())
const total = ref(0) // se conoce desde el primer bloque, no cambia despues
const pagina = ref(1)
const cargando = ref(false) // primer bloque: bloquea toda la pantalla
const cargandoBloque = ref(false) // bloque siguiente/anterior: solo el paginador
const error = ref<string | null>(null)
const sel = ref<Set<string>>(new Set())
// "Seleccionar toda la audiencia": la seleccion pasa a ser TODO el total del
// filtro (no solo los bloques cargados) menos los que se desmarquen a mano.
// Los envios en este modo mandan el filtro y el backend arma la lista completa.
const todaLaAudiencia = ref(false)

const indiceBloque = (p: number) => Math.floor(((p - 1) * POR_PAGINA) / TAMANO_BLOQUE)

// Contador de generacion: se incrementa cada vez que se aplica un filtro
// nuevo o se limpia. Cualquier peticion en curso de una generacion vieja
// (por ejemplo, le diste a "Aplicar" y antes de que respondiera le diste a
// "Limpiar") descarta su resultado al llegar en vez de sobreescribir el
// estado ya limpio/actualizado con datos viejos.
let generacion = 0

export function useSegmentador() {
  const totalPaginas = computed(() => Math.max(1, Math.ceil(total.value / POR_PAGINA)))
  const filtrados = computed(() => {
    const idx = indiceBloque(pagina.value)
    const bloque = bloques.value.get(idx) ?? []
    const desdeEnBloque = (pagina.value - 1) * POR_PAGINA - idx * TAMANO_BLOQUE
    return bloque.slice(desdeEnBloque, desdeEnBloque + POR_PAGINA)
  })
  const rangoDesde = computed(() => total.value === 0 ? 0 : (pagina.value - 1) * POR_PAGINA + 1)
  const rangoHasta = computed(() => Math.min(pagina.value * POR_PAGINA, total.value))

  // "Seleccion" solo cubre lo que ya se cargo (bloques vistos hasta ahora),
  // no toda la audiencia -- coherente con que no todo esta en memoria.
  const seleccion = computed(() =>
    [...bloques.value.values()].flat().filter(a => sel.value.has(a.id)),
  )
  const todoSel = computed(() => filtrados.value.length > 0 && filtrados.value.every(a => sel.value.has(a.id)))
  // Cargados y desmarcados (en modo "toda la audiencia" son las exclusiones).
  const excluidos = computed(() =>
    [...bloques.value.values()].flat().filter(a => !sel.value.has(a.id)),
  )
  const nSeleccionadas = computed(() =>
    todaLaAudiencia.value ? Math.max(0, total.value - excluidos.value.length) : seleccion.value.length,
  )
  const nFiltros = computed(() => contarFiltros(fApp.value))

  const asegurarBloque = async (idx: number) => {
    if (bloques.value.has(idx)) return
    const gen = generacion
    cargandoBloque.value = true
    try {
      const data = await getBloqueAudiencia(fApp.value, idx)
      if (gen !== generacion) return // se aplico/limpio un filtro mientras tanto: descartar
      bloques.value.set(idx, data.items)
      bloques.value = new Map(bloques.value)
      total.value = data.total
      const nuevaSel = new Set(sel.value)
      data.items.forEach(p => nuevaSel.add(p.id))
      sel.value = nuevaSel
    } finally {
      if (gen === generacion) cargandoBloque.value = false
    }
  }

  const aplicar = async () => {
    generacion++
    const gen = generacion
    fApp.value = clonarFiltro(f)
    bloques.value = new Map()
    total.value = 0
    pagina.value = 1
    sel.value = new Set()
    todaLaAudiencia.value = false
    error.value = null
    cargando.value = true
    try {
      await asegurarBloque(0)
    } catch (e) {
      if (gen !== generacion) return
      error.value = e instanceof Error ? e.message : 'No se pudo cargar la audiencia.'
    } finally {
      if (gen === generacion) cargando.value = false
    }
  }

  const limpiar = () => {
    generacion++ // invalida cualquier peticion en curso (ver asegurarBloque)
    Object.assign(f, filtroVacio())
    fApp.value = filtroVacio()
    bloques.value = new Map()
    total.value = 0
    pagina.value = 1
    error.value = null
    cargando.value = false
    cargandoBloque.value = false
    sel.value = new Set()
    todaLaAudiencia.value = false
  }

  /** Marca a toda la audiencia del filtro (incluye las páginas aún no cargadas). */
  const seleccionarTodaLaAudiencia = () => {
    sel.value = new Set([...bloques.value.values()].flat().map(a => a.id))
    todaLaAudiencia.value = true
  }
  const quitarSeleccion = () => {
    sel.value = new Set()
    todaLaAudiencia.value = false
  }

  const precargar = async (pre: Partial<FiltroSegmento>) => {
    Object.assign(f, filtroVacio(), pre)
    await aplicar()
  }

  const irAPagina = async (destino: number) => {
    if (cargandoBloque.value) return
    const objetivo = Math.min(Math.max(1, destino), totalPaginas.value)
    if (objetivo === pagina.value) return
    const gen = generacion
    try {
      await asegurarBloque(indiceBloque(objetivo))
      if (gen !== generacion) return
      pagina.value = objetivo
    } catch (e) {
      if (gen !== generacion) return
      error.value = e instanceof Error ? e.message : 'No se pudo cargar la audiencia.'
    }
  }
  const paginaAnterior = () => irAPagina(pagina.value - 1)
  const paginaSiguiente = () => irAPagina(pagina.value + 1)

  const toggleRow = (id: string) => {
    sel.value.has(id) ? sel.value.delete(id) : sel.value.add(id)
    sel.value = new Set(sel.value)
  }
  const toggleTodo = () => {
    const nueva = new Set(sel.value)
    if (todoSel.value) filtrados.value.forEach(a => nueva.delete(a.id))
    else filtrados.value.forEach(a => nueva.add(a.id))
    sel.value = nueva
  }

  return {
    f, fApp, sel, filtrados, seleccion, todoSel, nFiltros,
    todaLaAudiencia, excluidos, nSeleccionadas,
    total, pagina, totalPaginas, rangoDesde, rangoHasta, porPagina: POR_PAGINA,
    cargando, cargandoBloque, error,
    aplicar, limpiar, precargar, toggleRow, toggleTodo,
    seleccionarTodaLaAudiencia, quitarSeleccion,
    paginaAnterior, paginaSiguiente, irAPagina,
  }
}
