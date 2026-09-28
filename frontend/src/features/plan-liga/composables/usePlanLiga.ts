import { ref, computed, onMounted, watch } from 'vue'
import type {
  Beneficiario, BeneficiarioDraft, PlanServicio, Titular, TitularDraft,
  ReemplazoPersonaDraft, ReemplazoTitularResultado, ReemplazoBeneficiarioResultado,
} from '../types/plan-liga'
import { CUPO_MAXIMO, cupoMaximoTitular } from '../constants/plan-liga.constants'
import {
  createTitular, updateTitular, activarTitular, desactivarTitular,
  createBeneficiario, updateBeneficiario, getResumenTitulares,
  getListadoTitulares, getPlanesServicio, getTitular, getBeneficiariosTitular, exportarTitulares,
  activarBeneficiario as activarBeneficiarioApi, desactivarBeneficiario as desactivarBeneficiarioApi,
  reemplazarTitular as reemplazarTitularApi, reemplazarBeneficiario as reemplazarBeneficiarioApi,
  cambiarTitularBeneficiario as cambiarTitularBeneficiarioApi,
} from '../services/plan-liga.api'
import type { FiltrosTitulares } from '../services/plan-liga.api'

const TITULARES_POR_PAGINA = 6

export function usePlanLiga() {
  const titulares = ref<Titular[]>([])
  const cargandoTitulares = ref(false)
  const errorTitulares = ref<string | null>(null)
  const beneficiarios = ref<Beneficiario[]>([])

  const offsetTitulares = ref(0)
  const totalTitulares = ref(0)
  const paginaActual = computed(() => Math.floor(offsetTitulares.value / TITULARES_POR_PAGINA) + 1)
  const totalPaginas = computed(() => Math.max(1, Math.ceil(totalTitulares.value / TITULARES_POR_PAGINA)))
  const hayPaginaAnterior = computed(() => offsetTitulares.value > 0)
  const hayPaginaSiguiente = computed(() => offsetTitulares.value + TITULARES_POR_PAGINA < totalTitulares.value)

  const activosPorTitular = (id: number) =>
    beneficiarios.value.filter(b => b.titularId === id && b.estado === 'Activo').length
  const puedeAgregar = (id: number) => activosPorTitular(id) < CUPO_MAXIMO

  const buscar       = ref('')
  const filtroEstado = ref('todos')
  const filtroPlan   = ref<number | 'todos' | 'estandar'>('todos')
  const filtroSexo   = ref('todos')
  const filtroEdad   = ref('todos')

  const planesServicio = ref<PlanServicio[]>([])
  const cargarPlanesServicio = async () => {
    try {
      planesServicio.value = await getPlanesServicio()
    } catch {
      planesServicio.value = []
    }
  }

  // Mismos filtros para /listado (paginado) y /exportar (todo lo que los cumpla).
  const filtrosActivos = computed((): FiltrosTitulares => {
    const plan = filtroPlan.value
    return {
      estado: filtroEstado.value === 'todos' ? undefined : (filtroEstado.value as 'Activo' | 'Inactivo'),
      tipoPlanId: plan === 'todos' ? undefined : (plan === 'estandar' ? null : plan),
      // 'Otro' no tiene código en el backend (solo M/F), así que no se envía y no filtra.
      sexo: filtroSexo.value === 'Masculino' || filtroSexo.value === 'Femenino' ? filtroSexo.value : undefined,
      edad: filtroEdad.value === 'todos' ? undefined : (filtroEdad.value as '0-17' | '18-35' | '36-50' | '51+'),
      busqueda: buscar.value.trim() || undefined,
    }
  })

  // El agregado de beneficiarios que trae /listado (BENEFICIARIOS "activos/cupo") cuenta
  // TODOS los beneficiarios registrados del titular, sin filtrar por estado; por eso el
  // badge de la tabla puede mostrar más activos de los que realmente hay (ej. "5/4" cuando
  // en realidad 2 de esos 5 están inactivos). Se corrige por fila con el conteo real apenas
  // llega — son pocas peticiones porque la página solo tiene TITULARES_POR_PAGINA titulares.
  const sincronizarConteoRealTitular = async (t: Titular) => {
    try {
      const lista = await getBeneficiariosTitular(t.id, 'A')
      const activos = lista.length
      const idx = titulares.value.findIndex(x => x.id === t.id)
      if (idx === -1) return
      const actual = titulares.value[idx]
      titulares.value[idx] = {
        ...actual,
        planesDetalle: [{ nombre: actual.planesDetalle?.[0]?.nombre ?? '', activos, cupo: cupoMaximoTitular(actual) }],
      }
    } catch {
      // Si falla, se deja el valor (posiblemente impreciso) que trajo /listado.
    }
  }

  const cargarTitulares = async () => {
    cargandoTitulares.value = true
    errorTitulares.value = null
    try {
      const resultado = await getListadoTitulares({
        limit: TITULARES_POR_PAGINA,
        offset: offsetTitulares.value,
        ...filtrosActivos.value,
      })
      titulares.value = resultado.items
      totalTitulares.value = resultado.total
      titulares.value.forEach(t => sincronizarConteoRealTitular(t))
    } catch (e) {
      errorTitulares.value = e instanceof Error ? e.message : 'No se pudo cargar el listado de titulares.'
    } finally {
      cargandoTitulares.value = false
    }
  }

  const exportando = ref(false)
  const errorExportar = ref<string | null>(null)

  const exportarListado = async () => {
    exportando.value = true
    errorExportar.value = null
    try {
      const blob = await exportarTitulares(filtrosActivos.value)
      const url = URL.createObjectURL(blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = `titulares_beneficiarios_${new Date().toISOString().split('T')[0]}.xlsx`
      enlace.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      errorExportar.value = e instanceof Error ? e.message : 'No se pudo exportar el listado.'
    } finally {
      exportando.value = false
    }
  }

  const paginaSiguiente = () => {
    if (!hayPaginaSiguiente.value) return
    offsetTitulares.value += TITULARES_POR_PAGINA
    cargarTitulares()
  }
  const paginaAnterior = () => {
    if (!hayPaginaAnterior.value) return
    offsetTitulares.value = Math.max(0, offsetTitulares.value - TITULARES_POR_PAGINA)
    cargarTitulares()
  }

  watch([filtroEstado, filtroPlan, filtroSexo, filtroEdad], () => {
    offsetTitulares.value = 0
    cargarTitulares()
  })

  // La búsqueda se debounce para no disparar una petición por cada tecla.
  let busquedaTimeout: ReturnType<typeof setTimeout> | undefined
  watch(buscar, () => {
    clearTimeout(busquedaTimeout)
    busquedaTimeout = setTimeout(() => {
      offsetTitulares.value = 0
      cargarTitulares()
    }, 350)
  })

  const totalActivos = ref(0)
  const totalBeneficiarios = ref(0)
  const errorResumen = ref<string | null>(null)

  const cargarResumen = async () => {
    errorResumen.value = null
    try {
      const data = await getResumenTitulares()
      totalActivos.value = data.titulares_activos
      totalBeneficiarios.value = data.beneficiarios_activos
    } catch (e) {
      errorResumen.value = e instanceof Error ? e.message : 'No se pudo cargar el resumen de titulares.'
    }
  }

  onMounted(() => {
    cargarResumen()
    cargarTitulares()
    cargarPlanesServicio()
  })

  const titularesTope      = computed(() => titulares.value.filter(t => activosPorTitular(t.id) >= CUPO_MAXIMO).length)

  const cargandoDetalleTitular = ref(false)
  const obtenerTitular = async (id: number): Promise<Titular | null> => {
    cargandoDetalleTitular.value = true
    try {
      return await getTitular(id)
    } catch {
      return null
    } finally {
      cargandoDetalleTitular.value = false
    }
  }

  const guardandoTitular = ref(false)
  const errorGuardarTitular = ref<string | null>(null)

  const crearTitular = async (data: TitularDraft): Promise<boolean> => {
    guardandoTitular.value = true
    errorGuardarTitular.value = null
    try {
      await createTitular(data)
      offsetTitulares.value = 0
      await cargarTitulares()
      cargarResumen()
      return true
    } catch (e) {
      errorGuardarTitular.value = e instanceof Error ? e.message : 'No se pudo crear el titular.'
      return false
    } finally {
      guardandoTitular.value = false
    }
  }

  const actualizarTitular = async (id: number, data: TitularDraft): Promise<boolean> => {
    guardandoTitular.value = true
    errorGuardarTitular.value = null
    try {
      const actualizado = await updateTitular(id, data)
      const idx = titulares.value.findIndex(t => t.id === id)
      if (idx !== -1) titulares.value[idx] = actualizado
      return true
    } catch (e) {
      errorGuardarTitular.value = e instanceof Error ? e.message : 'No se pudo actualizar el titular.'
      return false
    } finally {
      guardandoTitular.value = false
    }
  }
  // Nombre a mostrar del plan elegido (tipoPlanId null = Plan Estándar); usado tanto para
  // mandar TIPO_PLAN al backend como para reflejar el cambio en memoria sin recargar.
  const nombrePlan = (tipoPlanId: number | null) =>
    tipoPlanId === null ? 'Estándar' : (planesServicio.value.find(p => p.id === tipoPlanId)?.nombre ?? '')

  const toggleEstadoTitular = async (
    t: Titular,
    fechaIngreso?: string,
    aplicarAGrupo = true,
    // Cambio de plan al renovar (solo aplica al activar, no al desactivar).
    cambiarPlan = false,
    tipoPlanId: number | null = null,
  ) => {
    const activando = t.estado !== 'Activo'
    const nuevoEstado = activando ? 'Activo' : 'Inactivo'
    guardandoTitular.value = true
    errorGuardarTitular.value = null
    try {
      if (activando) {
        await activarTitular(t.id, fechaIngreso!, aplicarAGrupo, cambiarPlan, nombrePlan(tipoPlanId), tipoPlanId)
      } else {
        await desactivarTitular(t.id)
      }
      const idx = titulares.value.findIndex(x => x.id === t.id)
      if (idx !== -1) {
        titulares.value[idx] = {
          ...t,
          estado: nuevoEstado,
          ...(activando && cambiarPlan ? { tipoPlanId, tipoPlan: nombrePlan(tipoPlanId) } : {}),
        }
      }
      cargarResumen()
    } catch (e) {
      errorGuardarTitular.value = e instanceof Error
        ? e.message
        : `No se pudo ${activando ? 'activar' : 'desactivar'} el titular.`
    } finally {
      guardandoTitular.value = false
    }
  }

  // A diferencia de toggleEstadoTitular (que decide activar/desactivar segun el
  // estado actual), esto SIEMPRE llama a activarTitular sin importar si el
  // titular ya estaba activo o no: el backend de todas formas fija estado=Activo,
  // FECHA_INGRESO y RENOVADO='S' en la misma operacion (repository.py:812-820),
  // asi que reusarlo tambien sirve para solo "editar" la fecha de un titular que
  // ya esta activo (queda activo igual, solo cambia la fecha).
  const editarFechaIngresoTitular = async (t: Titular, fechaIngreso: string, aplicarAGrupo = true) => {
    guardandoTitular.value = true
    errorGuardarTitular.value = null
    try {
      await activarTitular(t.id, fechaIngreso, aplicarAGrupo)
      const idx = titulares.value.findIndex(x => x.id === t.id)
      if (idx !== -1) titulares.value[idx] = { ...t, estado: 'Activo', fechaInscripcion: fechaIngreso }
      cargarResumen()
    } catch (e) {
      errorGuardarTitular.value = e instanceof Error ? e.message : 'No se pudo actualizar la fecha de inscripción.'
    } finally {
      guardandoTitular.value = false
    }
  }

  const reemplazandoTitular = ref(false)
  const errorReemplazarTitular = ref<string | null>(null)
  const resultadoReemplazoTitular = ref<ReemplazoTitularResultado | null>(null)

  // Reemplazo != edición: da de baja al titular actual y da de alta a una persona nueva en
  // su lugar (más Servinte). Por eso, a diferencia de actualizarTitular, se refresca el
  // listado completo en vez de parchar en memoria: cambian estado del anterior, aparece
  // un titular nuevo con otro id, y puede no seguir cayendo en la página actual.
  const reemplazarTitularAccion = async (t: Titular, data: ReemplazoPersonaDraft): Promise<boolean> => {
    reemplazandoTitular.value = true
    errorReemplazarTitular.value = null
    try {
      resultadoReemplazoTitular.value = await reemplazarTitularApi(t.id, data)
      await cargarTitulares()
      cargarResumen()
      return true
    } catch (e) {
      errorReemplazarTitular.value = e instanceof Error ? e.message : 'No se pudo reemplazar el titular.'
      return false
    } finally {
      reemplazandoTitular.value = false
    }
  }

  // Activar/desactivar/crear un beneficiario desde el drawer no vuelve a pedir el listado
  // completo de titulares (sería un roundtrip innecesario); sin este ajuste, el conteo de
  // "activos" que muestra la tabla (viene de planesDetalle, calculado en el backend al
  // momento del listado) queda desactualizado hasta que algo más refresque la página.
  const ajustarConteoActivosTitular = (titularId: number, delta: number) => {
    const idx = titulares.value.findIndex(t => t.id === titularId)
    const planes = titulares.value[idx]?.planesDetalle
    if (idx === -1 || !planes?.length) return
    titulares.value[idx] = {
      ...titulares.value[idx],
      planesDetalle: planes.map((p, i) => i === 0 ? { ...p, activos: Math.max(0, p.activos + delta) } : p),
    }
  }

  const beneficiariosDeTitular = (titularId: number) =>
    beneficiarios.value.filter(b => b.titularId === titularId)

  const beneficiariosTitular = ref<Beneficiario[]>([])
  const cargandoBeneficiariosTitular = ref(false)
  const errorBeneficiariosTitular = ref<string | null>(null)
  /** Filtro del drawer: A = activos, I = inactivos. */
  const filtroEstadoBeneficiarios = ref<'A' | 'I'>('A')
  /** Conteo de activos para el cupo (no depende del filtro visible). */
  const activosBeneficiariosCount = ref(0)
  let cargaBeneficiariosSeq = 0

  const cargarBeneficiariosTitular = async (
    titularId: number,
    estado: 'A' | 'I' = filtroEstadoBeneficiarios.value,
  ) => {
    const seq = ++cargaBeneficiariosSeq
    if (filtroEstadoBeneficiarios.value !== estado) {
      filtroEstadoBeneficiarios.value = estado
    }
    cargandoBeneficiariosTitular.value = true
    errorBeneficiariosTitular.value = null
    // Limpia la lista al instante para no mostrar activos cuando se pide inactivos (y viceversa).
    beneficiariosTitular.value = []
    try {
      const lista = await getBeneficiariosTitular(titularId, estado)
      if (seq !== cargaBeneficiariosSeq) return
      beneficiariosTitular.value = lista
      if (estado === 'A') activosBeneficiariosCount.value = lista.length
    } catch (e) {
      if (seq !== cargaBeneficiariosSeq) return
      errorBeneficiariosTitular.value = e instanceof Error ? e.message : 'No se pudo cargar los beneficiarios del titular.'
      beneficiariosTitular.value = []
    } finally {
      if (seq === cargaBeneficiariosSeq) cargandoBeneficiariosTitular.value = false
    }
  }

  const guardandoBeneficiario = ref(false)
  const errorGuardarBeneficiario = ref<string | null>(null)

  const crearBeneficiario = async (titularId: number, data: BeneficiarioDraft): Promise<boolean> => {
    guardandoBeneficiario.value = true
    errorGuardarBeneficiario.value = null
    try {
      await createBeneficiario(titularId, data)
      await cargarBeneficiariosTitular(titularId)
      if (data.estado === 'Activo') {
        ajustarConteoActivosTitular(titularId, 1)
        if (filtroEstadoBeneficiarios.value === 'I') {
          activosBeneficiariosCount.value += 1
        }
      }
      cargarResumen()
      return true
    } catch (e) {
      errorGuardarBeneficiario.value = e instanceof Error ? e.message : 'No se pudo crear el beneficiario.'
      return false
    } finally {
      guardandoBeneficiario.value = false
    }
  }

  const actualizarBeneficiario = async (titularId: number, id: number, data: BeneficiarioDraft): Promise<boolean> => {
    guardandoBeneficiario.value = true
    errorGuardarBeneficiario.value = null
    try {
      const actualizado = await updateBeneficiario(titularId, id, data)
      const idx = beneficiariosTitular.value.findIndex(b => b.id === id)
      if (idx !== -1) beneficiariosTitular.value[idx] = actualizado
      return true
    } catch (e) {
      errorGuardarBeneficiario.value = e instanceof Error ? e.message : 'No se pudo actualizar el beneficiario.'
      return false
    } finally {
      guardandoBeneficiario.value = false
    }
  }

  const reemplazandoBeneficiario = ref(false)
  const errorReemplazarBeneficiario = ref<string | null>(null)
  const resultadoReemplazoBeneficiario = ref<ReemplazoBeneficiarioResultado | null>(null)

  // Igual que reemplazarTitularAccion: se refresca la lista de beneficiarios del titular en
  // vez de parchar en memoria, porque el anterior cambia de estado y aparece uno nuevo con otro id.
  const reemplazarBeneficiarioAccion = async (titularId: number, b: Beneficiario, data: ReemplazoPersonaDraft): Promise<boolean> => {
    reemplazandoBeneficiario.value = true
    errorReemplazarBeneficiario.value = null
    try {
      resultadoReemplazoBeneficiario.value = await reemplazarBeneficiarioApi(titularId, b.id, data)
      await cargarBeneficiariosTitular(titularId)
      cargarResumen()
      return true
    } catch (e) {
      errorReemplazarBeneficiario.value = e instanceof Error ? e.message : 'No se pudo reemplazar el beneficiario.'
      return false
    } finally {
      reemplazandoBeneficiario.value = false
    }
  }

  const cambiandoTitularBeneficiario = ref(false)
  const errorCambiarTitularBeneficiario = ref<string | null>(null)

  // Mueve al beneficiario a otro titular (por documento). El titular actual pierde un activo
  // (se refresca su drawer y su fila en la tabla); el titular nuevo, si ya está cargado en la
  // página actual, gana uno — si no está en la página visible, su fila se corrige sola la
  // próxima vez que se cargue (sincronizarConteoRealTitular).
  const cambiarTitularBeneficiarioAccion = async (titularActualId: number, b: Beneficiario, documentoTitularNuevo: string): Promise<boolean> => {
    cambiandoTitularBeneficiario.value = true
    errorCambiarTitularBeneficiario.value = null
    try {
      await cambiarTitularBeneficiarioApi(b.id, documentoTitularNuevo)
      await cargarBeneficiariosTitular(titularActualId)
      // Solo mueve el conteo de "activos" si el beneficiario contaba como tal antes del cambio.
      if (b.estado === 'Activo') {
        ajustarConteoActivosTitular(titularActualId, -1)
        const titularNuevo = titulares.value.find(t => t.documento === documentoTitularNuevo)
        if (titularNuevo) ajustarConteoActivosTitular(titularNuevo.id, 1)
      }
      cargarResumen()
      return true
    } catch (e) {
      errorCambiarTitularBeneficiario.value = e instanceof Error ? e.message : 'No se pudo cambiar el titular del beneficiario.'
      return false
    } finally {
      cambiandoTitularBeneficiario.value = false
    }
  }

  const guardandoEstadoBeneficiario = ref(false)
  const errorEstadoBeneficiario = ref<string | null>(null)

  const activarEstadoBeneficiario = async (titularId: number, b: Beneficiario, fechaIngreso: string) => {
    guardandoEstadoBeneficiario.value = true
    errorEstadoBeneficiario.value = null
    try {
      await activarBeneficiarioApi(titularId, b.id, fechaIngreso)
      ajustarConteoActivosTitular(titularId, 1)
      if (filtroEstadoBeneficiarios.value === 'I') {
        activosBeneficiariosCount.value += 1
      }
      await cargarBeneficiariosTitular(titularId)
      cargarResumen()
    } catch (e) {
      errorEstadoBeneficiario.value = e instanceof Error ? e.message : 'No se pudo activar el beneficiario.'
    } finally {
      guardandoEstadoBeneficiario.value = false
    }
  }

  const desactivarEstadoBeneficiario = async (titularId: number, b: Beneficiario) => {
    guardandoEstadoBeneficiario.value = true
    errorEstadoBeneficiario.value = null
    try {
      await desactivarBeneficiarioApi(titularId, b.id)
      ajustarConteoActivosTitular(titularId, -1)
      if (filtroEstadoBeneficiarios.value === 'I') {
        activosBeneficiariosCount.value = Math.max(0, activosBeneficiariosCount.value - 1)
      }
      await cargarBeneficiariosTitular(titularId)
      cargarResumen()
    } catch (e) {
      errorEstadoBeneficiario.value = e instanceof Error ? e.message : 'No se pudo desactivar el beneficiario.'
    } finally {
      guardandoEstadoBeneficiario.value = false
    }
  }

  return {
    titulares, beneficiarios,
    buscar, filtroEstado, filtroPlan, filtroSexo, filtroEdad,
    planesServicio, cargandoTitulares, errorTitulares,
    totalActivos, totalBeneficiarios, titularesTope, errorResumen,
    totalTitulares, paginaActual, totalPaginas, hayPaginaAnterior, hayPaginaSiguiente,
    paginaSiguiente, paginaAnterior,
    exportarListado, exportando, errorExportar,
    activosPorTitular, puedeAgregar,
    cargandoDetalleTitular, obtenerTitular,
    crearTitular, actualizarTitular, toggleEstadoTitular, editarFechaIngresoTitular,
    guardandoTitular, errorGuardarTitular,
    reemplazarTitularAccion, reemplazandoTitular, errorReemplazarTitular, resultadoReemplazoTitular,
    beneficiariosDeTitular, crearBeneficiario, actualizarBeneficiario,
    guardandoBeneficiario, errorGuardarBeneficiario,
    activarEstadoBeneficiario, desactivarEstadoBeneficiario,
    guardandoEstadoBeneficiario, errorEstadoBeneficiario,
    reemplazarBeneficiarioAccion, reemplazandoBeneficiario, errorReemplazarBeneficiario, resultadoReemplazoBeneficiario,
    cambiarTitularBeneficiarioAccion, cambiandoTitularBeneficiario, errorCambiarTitularBeneficiario,
    beneficiariosTitular, cargandoBeneficiariosTitular, errorBeneficiariosTitular, cargarBeneficiariosTitular,
    filtroEstadoBeneficiarios, activosBeneficiariosCount,
  }
}
