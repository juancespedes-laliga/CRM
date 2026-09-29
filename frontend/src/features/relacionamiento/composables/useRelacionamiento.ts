import { ref, computed, onMounted, watch } from 'vue'
import type { Actividad, ActividadDraft, TipoActividad } from '../types/actividad'
import { getActividades, createActividad, updateActividad, completarActividad, deleteActividad } from '../services/relacionamiento.api'

const PAGE_SIZE = 4

export function useRelacionamiento() {
  const actividades = ref<Actividad[]>([])
  const cargando = ref(false)
  const error = ref<string | null>(null)

  const cargarActividades = async () => {
    cargando.value = true
    error.value = null
    try {
      actividades.value = await getActividades()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'No se pudo cargar la bitácora.'
    } finally {
      cargando.value = false
    }
  }

  onMounted(cargarActividades)

  const filtroTipo = ref<TipoActividad | 'todos'>('todos')
  const filtroUsuario = ref('todos')
  const buscar = ref('')

  // Sin espacios en ninguno de los dos lados: una cédula guardada/escrita como
  // "123 456 789" tiene que matchear igual que "123456789" o "123 456789".
  const sinEspacios = (s: string) => s.replace(/\s+/g, '')

  const actividadesFiltradas = computed(() =>
    actividades.value.filter(a => {
      const q = sinEspacios(buscar.value.toLowerCase())
      const matchBuscar = !q || [
        a.contactoNombre, a.empresaNombre, a.titularNombre, a.accion,
        a.contactoDocumento, a.titularDocumento,
      ].some(f => sinEspacios(f.toLowerCase()).includes(q))
      return matchBuscar
        && (filtroTipo.value === 'todos' || a.tipo === filtroTipo.value)
        && (filtroUsuario.value === 'todos' || a.usuario === filtroUsuario.value)
    })
  )

  const usuarios = computed(() => [...new Set(actividades.value.map(a => a.usuario).filter(Boolean))].sort())

  const paginaActual = ref(1)
  const porPagina    = PAGE_SIZE
  const actividadesPaginadas = computed(() => {
    const start = (paginaActual.value - 1) * porPagina
    return actividadesFiltradas.value.slice(start, start + porPagina)
  })
  const totalPaginas = computed(() => Math.ceil(actividadesFiltradas.value.length / porPagina))

  // Igual que en Contactos: si cambia la búsqueda o algún filtro, se vuelve a la página 1.
  watch([buscar, filtroTipo, filtroUsuario], () => { paginaActual.value = 1 })

  const guardandoActividad = ref(false)
  const errorGuardarActividad = ref<string | null>(null)

  const crearActividad = async (data: ActividadDraft): Promise<boolean> => {
    guardandoActividad.value = true
    errorGuardarActividad.value = null
    try {
      await createActividad(data)
      await cargarActividades()
      return true
    } catch (e) {
      errorGuardarActividad.value = e instanceof Error ? e.message : 'No se pudo registrar la actividad.'
      return false
    } finally {
      guardandoActividad.value = false
    }
  }

  const actualizarActividad = async (id: number, data: ActividadDraft): Promise<boolean> => {
    guardandoActividad.value = true
    errorGuardarActividad.value = null
    try {
      await updateActividad(id, data)
      await cargarActividades()
      return true
    } catch (e) {
      errorGuardarActividad.value = e instanceof Error ? e.message : 'No se pudo actualizar la actividad.'
      return false
    } finally {
      guardandoActividad.value = false
    }
  }

  // ─── Pendientes: actividades con próximo paso aún no completado, para la alarma de
  // seguimientos. "estado" es la fuente de verdad (completarActividad ya no borra el texto
  // del próximo paso, solo cambia estado a 'realizado'), proximoPaso solo filtra legado.
  const pendientes = computed(() =>
    actividades.value
      .filter(a => !!a.proximoPaso && a.estado === 'pendiente')
      .sort((a, b) => (a.proximoPasoFecha || '9999-99-99').localeCompare(b.proximoPasoFecha || '9999-99-99'))
  )

  const completandoId = ref<number | null>(null)
  const errorCompletarActividad = ref<string | null>(null)

  const marcarRealizada = async (id: number): Promise<boolean> => {
    completandoId.value = id
    errorCompletarActividad.value = null
    try {
      await completarActividad(id)
      await cargarActividades()
      return true
    } catch (e) {
      errorCompletarActividad.value = e instanceof Error ? e.message : 'No se pudo marcar la actividad como realizada.'
      return false
    } finally {
      completandoId.value = null
    }
  }

  const eliminandoActividad = ref(false)
  const errorEliminarActividad = ref<string | null>(null)

  const eliminarActividad = async (id: number): Promise<boolean> => {
    eliminandoActividad.value = true
    errorEliminarActividad.value = null
    try {
      await deleteActividad(id)
      actividades.value = actividades.value.filter(a => a.id !== id)
      return true
    } catch (e) {
      errorEliminarActividad.value = e instanceof Error ? e.message : 'No se pudo eliminar la actividad.'
      return false
    } finally {
      eliminandoActividad.value = false
    }
  }

  return {
    actividades, cargando, error,
    filtroTipo, filtroUsuario, buscar,
    actividadesFiltradas, usuarios,
    paginaActual, porPagina, actividadesPaginadas, totalPaginas,
    crearActividad, actualizarActividad, guardandoActividad, errorGuardarActividad,
    eliminarActividad, eliminandoActividad, errorEliminarActividad,
    pendientes, marcarRealizada, completandoId, errorCompletarActividad,
  }
}
