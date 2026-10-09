<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'

// --- INTERFACES ---
interface ServicioParticular { nombre: string; fecha: string; estado: 'Activo' | 'Terminado'; }
interface Beneficiario { nombreCompleto: string; tipoDocumento: string; documento: string; edad: number; genero: string; telefono?: string; parentesco: string; }
interface Contacto { idUnico: string; nombreCompleto: string; rol: 'titular' | 'beneficiario'; tipoDocumento: string; documento: string; telefono: string; whatsapp: string; email: string; ciudad: string; pais: string; canalOrigen: string; campana: string; estadoLead: string; ultimoContacto: string; proximoContacto: string; cantidadLlamadas: number; cantidadEmails: number; notes?: string; edad: number; genero: string; serviciosHistoricos: ServicioParticular[]; beneficiariosAsociados?: Beneficiario[]; }

// --- PROPS Y EMITS ---
const props = defineProps<{
  contactosFiltrados: Contacto[]
  contactoSeleccionado: Contacto | null
  modoVista: 'general' | 'particular'
  busqueda: string
  filtroRol: string
  filtroEstado: string
  filtroOrigen: string
  filtroCampana: string
  filtroEdad: string
}>()

const emit = defineEmits<{
  (e: 'seleccionar', contacto: Contacto): void
  (e: 'guardarNuevoProspecto', nuevoContacto: Partial<Contacto>): void
  (e: 'update:busqueda', val: string): void
  (e: 'update:filtroRol', val: string): void
  (e: 'update:filtroEstado', val: string): void
  (e: 'update:filtroOrigen', val: string): void
  (e: 'update:filtroCampana', val: string): void
  (e: 'update:filtroEdad', val: string): void
  (e: 'procesarCargaMasiva', data: { seccion: string; accion: string; maxPersonas?: number; archivo: File | null }): void
  (e: 'descargarPlantilla', seccion: string): void
}>()

// --- ESTADOS DE CONFIGURACIÓN DE CARGAS ---
const accionTitularesUnicos = ref('Activar')     
const accionDocumento = ref('Activar')          
const accionTitularInscripcion = ref('Activar') 
const maxPersonasInscripcion = ref(5)          

// --- ESTADO MENÚ DESPLEGABLE (CARGA MASIVA) ---
const cargaMasivaAbierta = ref(false)
const seccionActiva = ref<'titulares' | 'beneficiarios' | 'inscripcion' | 'remplazo' | null>('titulares')

const cargaTop = ref(0)
const cargaLeft = ref(0)

const alternarCargaMasiva = (event: MouseEvent) => {
  cargaMasivaAbierta.value = !cargaMasivaAbierta.value
  if (cargaMasivaAbierta.value) {
    const target = event.currentTarget as HTMLElement
    if (target) {
      const rect = target.getBoundingClientRect()
      cargaTop.value = rect.top
      cargaLeft.value = rect.right + 8 
    }
  }
}

// --- CONFIRMACIÓN PARA CARGAS MASIVAS DE DESACTIVACIÓN ---
const confirmarDesactivarAbierto = ref(false)
const cargaPendiente = ref<{ seccion: string; accion: string; maxPersonas?: number; archivo: File } | null>(null)

const manejarArchivo = (event: Event, seccion: string) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    let accionFinal = 'Inscribir'
    let maxPersonasFinal: number | undefined = undefined

    if (seccion === 'titulares') {
      accionFinal = accionTitularesUnicos.value
    } else if (seccion === 'beneficiarios') {
      accionFinal = accionDocumento.value
    } else if (seccion === 'inscripcion') {
      accionFinal = accionTitularInscripcion.value
      maxPersonasFinal = maxPersonasInscripcion.value
    }

    const payload = { seccion, accion: accionFinal, maxPersonas: maxPersonasFinal, archivo: target.files[0] }
    target.value = ''

    if (accionFinal === 'Desactivar') {
      cargaPendiente.value = payload
      confirmarDesactivarAbierto.value = true
      return
    }

    emit('procesarCargaMasiva', payload)
    cargaMasivaAbierta.value = false
  }
}

const confirmarCargaDesactivar = () => {
  if (cargaPendiente.value) emit('procesarCargaMasiva', cargaPendiente.value)
  cargaPendiente.value = null
  confirmarDesactivarAbierto.value = false
  cargaMasivaAbierta.value = false
}

const cancelarCargaDesactivar = () => {
  cargaPendiente.value = null
  confirmarDesactivarAbierto.value = false
}

// --- ESTADO DEL MODAL AGREGAR PROSPECTO ---
const modalAgregarAbierto = ref(false)
const nuevoProspecto = ref({
  nombreCompleto: '', tipoDocumento: 'CC', documento: '', telefono: '', whatsapp: '', email: '', canalOrigen: 'Llamada Directa', campana: 'Registro Manual', estadoLead: 'Prospecto', rol: 'titular' as 'titular'
})

const cerrarModalProspecto = () => {
  modalAgregarAbierto.value = false
  nuevoProspecto.value = {
    nombreCompleto: '', tipoDocumento: 'CC', documento: '', telefono: '', whatsapp: '', email: '', canalOrigen: 'Llamada Directa', campana: 'Registro Manual', estadoLead: 'Prospecto', rol: 'titular'
  }
}

const procesarGuardado = () => {
  if (!nuevoProspecto.value.nombreCompleto || !nuevoProspecto.value.documento) {
    alert('Por favor, ingresa al menos el Nombre y el Documento.')
    return
  }
  emit('guardarNuevoProspecto', { ...nuevoProspecto.value, idUnico: 'ID-' + Date.now() })
  cerrarModalProspecto()
}

// --- CONTADORES TOTALES ---
const totalProspectos = computed(() => {
  return props.contactosFiltrados.filter(c => c.estadoLead === 'Prospecto').length
})

// --- CONTROL DE MENÚS FILTROS ---
const filtrosAbiertos = ref(false)
const subMenuActivo = ref<'rol' | 'estado' | 'origen' | 'campana' | 'edad' | null>(null)
const menuTop = ref(0)
const menuLeft = ref(0)

const subMenuTop = ref(0)
const subMenuLeft = ref(0)

const alternarMenuPrincipal = (event: MouseEvent) => {
  filtrosAbiertos.value = !filtrosAbiertos.value
  if (filtrosAbiertos.value) {
    subMenuActivo.value = null 
    const target = event.currentTarget as HTMLElement
    if (target) {
      const rect = target.getBoundingClientRect()
      menuTop.value = rect.top
      menuLeft.value = rect.right + 8 
    }
  }
}

const abrirSubMenu = (event: MouseEvent, tipo: 'rol' | 'estado' | 'origen' | 'campana' | 'edad') => {
  if (subMenuActivo.value === tipo) {
    subMenuActivo.value = null
    return
  }
  subMenuActivo.value = tipo
  const target = event.currentTarget as HTMLElement
  if (target) {
    const rect = target.getBoundingClientRect()
    subMenuTop.value = rect.top - 4 
    subMenuLeft.value = rect.right + 8 
  }
}

const clickAfueraDetectado = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (filtrosAbiertos.value && !target.closest('.btn-ajustes-trigger') && !target.closest('.panel-flotante-root') && !target.closest('.panel-sub-flotante')) {
    filtrosAbiertos.value = false
    subMenuActivo.value = null
  }
  if (cargaMasivaAbierta.value && !target.closest('.btn-carga-trigger') && !target.closest('.panel-carga-flotante')) {
    cargaMasivaAbierta.value = false
  }
}

onMounted(() => document.addEventListener('click', clickAfueraDetectado))
onUnmounted(() => document.removeEventListener('click', clickAfueraDetectado))

const conteoFiltrosActivos = computed(() => {
  let activos = 0
  if (filtroRolLocal.value !== 'todos') activos++
  if (filtroEstadoLocal.value !== 'todos') activos++
  if (filtroOrigenLocal.value !== 'todos') activos++
  if (filtroCampanaLocal.value !== 'todos') activos++
  if (filtroEdadLocal.value !== 'todos') activos++
  return activos
})

// --- WATCHERS DE SINCRONIZACIÓN ---
const busquedaLocal = ref(props.busqueda)
const filtroRolLocal = ref(props.filtroRol)
const filtroEstadoLocal = ref(props.filtroEstado)
const filtroOrigenLocal = ref(props.filtroOrigen)
const filtroCampanaLocal = ref(props.filtroCampana)
const filtroEdadLocal = ref(props.filtroEdad)

watch(() => props.busqueda, (val) => busquedaLocal.value = val)
watch(() => props.filtroRol, (val) => filtroRolLocal.value = val)
watch(() => props.filtroEstado, (val) => filtroEstadoLocal.value = val)
watch(() => props.filtroOrigen, (val) => filtroOrigenLocal.value = val)
watch(() => props.filtroCampana, (val) => filtroCampanaLocal.value = val)
watch(() => props.filtroEdad, (val) => filtroEdadLocal.value = val)

watch(busquedaLocal, (val) => emit('update:busqueda', val))
watch(filtroRolLocal, (val) => emit('update:filtroRol', val))
watch(filtroEstadoLocal, (val) => emit('update:filtroEstado', val))
watch(filtroOrigenLocal, (val) => emit('update:filtroOrigen', val))
watch(filtroCampanaLocal, (val) => emit('update:filtroCampana', val))
watch(filtroEdadLocal, (val) => emit('update:filtroEdad', val))

const contactosRenderizados = computed(() => {
  if (filtroEstadoLocal.value === 'Prospecto') {
    return props.contactosFiltrados.filter(c => c.estadoLead === 'Prospecto')
  }
  return props.contactosFiltrados
})

// Textos legibles dinámicos
const textoRolActivo = computed(() => {
  if (filtroRolLocal.value === 'titular') return 'Titulares'
  if (filtroRolLocal.value === 'beneficiario') return 'Beneficiarios'
  return 'Filtrar por Rol'
})

const textoEstadoActivo = computed(() => {
  if (filtroEstadoLocal.value === 'Prospecto') return 'Solo Prospectos'
  if (filtroEstadoLocal.value === 'Cliente') return 'Solo Clientes'
  return 'Filtrar por Estado'
})

const textoOrigenActivo = computed(() => {
  if (filtroOrigenLocal.value === 'todos') return 'Canal de Origen'
  return filtroOrigenLocal.value
})

const textoCampanaActiva = computed(() => {
  if (filtroCampanaLocal.value === 'todos') return 'Filtrar Campaña'
  if (filtroCampanaLocal.value === 'Registro Manual') return 'Manual'
  if (filtroCampanaLocal.value === 'Campaña Black Friday') return 'Black Friday'
  return 'Orgánica'
})

const textoEdadActiva = computed(() => {
  if (filtroEdadLocal.value === 'menores') return 'Menores (< 18)'
  if (filtroEdadLocal.value === 'adultos') return 'Adultos (18 - 60)'
  if (filtroEdadLocal.value === 'mayores') return 'Mayores (> 60)'
  return 'Rango de Edad'
})
</script>

<template>
  <div class="px-4 py-3 surface-header border-b border-default flex justify-between items-center shrink-0 rounded-t-xl relative z-10">
    <span class="text-[10px] font-black uppercase text-subtle tracking-widest">Bandeja de Inteligencia</span>
    <span class="text-[10px] bg-blue-700 text-white font-mono px-2 py-0.5 rounded-md font-black shadow-xs">
      {{ contactosRenderizados.length }}
    </span>
  </div>

  <div class="p-3 bg-white dark:bg-slate-800 border-b border-slate-100 dark:border-slate-700 shrink-0 relative z-20 space-y-2">
    <div class="flex gap-2">
      <div class="relative flex-1">
        <input
          v-model="busquedaLocal" type="text" placeholder="Buscar Cédula, Nombre..."
          class="w-full input-surface placeholder-slate-400 dark:placeholder-slate-500 rounded-lg px-3 py-2 text-xs focus:outline-none focus:bg-white dark:focus:bg-slate-800 focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all shadow-inner"
        />
      </div>

      <button
        type="button" @click="modalAgregarAbierto = true" title="Agregar Nuevo Prospecto"
        class="h-full px-3 bg-blue-600 text-white hover:bg-blue-700 active:scale-95 rounded-lg text-xs font-black transition-all flex items-center justify-center cursor-pointer select-none shrink-0 shadow-sm border border-blue-700"
      >
        <span>➕</span>
      </button>

      <button
        type="button" @click="alternarMenuPrincipal"
        :class="['btn-ajustes-trigger h-full px-2.5 rounded-lg border text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer select-none shrink-0', filtrosAbiertos || conteoFiltrosActivos > 0 ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800 text-slate-900 font-bold dark:text-white shadow-xs' : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700']"
      >
        <span>⚙️</span>
        <span v-if="conteoFiltrosActivos > 0" class="bg-blue-600 text-white text-[9px] font-black px-1.5 py-0.5 rounded-full leading-none">
          {{ conteoFiltrosActivos }}
        </span>
        <span class="text-[8px] font-mono transition-transform duration-200" :class="{ 'rotate-180': filtrosAbiertos }">▼</span>
      </button>
    </div>

    <div class="flex border border-slate-200/60 dark:border-slate-700 p-0.5 bg-slate-50 dark:bg-slate-900 rounded-lg gap-0.5">
      <button
        @click="filtroEstadoLocal = 'todos'"
        :class="['flex-1 py-1.5 px-2 rounded-md text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer flex items-center justify-center gap-1.5', filtroEstadoLocal !== 'Prospecto' ? 'bg-white dark:bg-slate-800 text-slate-900 font-bold dark:text-white shadow-xs' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200']"
      >
        <span>Contactos</span>
        <span :class="['px-1.5 py-0.5 font-mono text-[9px] rounded-md font-bold', filtroEstadoLocal !== 'Prospecto' ? 'bg-blue-100 dark:bg-blue-900/60 text-slate-900 font-bold dark:text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300']">
          {{ contactosFiltrados.length }}
        </span>
      </button>

      <button
        @click="filtroEstadoLocal = 'Prospecto'"
        :class="['flex-1 py-1.5 px-2 rounded-md text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer flex items-center justify-center gap-1.5', filtroEstadoLocal === 'Prospecto' ? 'bg-white dark:bg-slate-800 text-amber-700 dark:text-amber-400 shadow-xs border border-slate-100 dark:border-slate-700' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200']"
      >
        <span>Prospectos</span>
        <span :class="['px-1.5 py-0.5 font-mono text-[9px] rounded-md font-bold', filtroEstadoLocal === 'Prospecto' ? 'bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300' : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300']">
          {{ totalProspectos }}
        </span>
      </button>
    </div>
  </div>

  <div class="px-3 pt-2 pb-1 shrink-0 bg-white dark:bg-slate-800">
    <div
      @click="alternarCargaMasiva"
      :class="['btn-carga-trigger w-full flex justify-between items-center py-2 px-3 border rounded-xl cursor-pointer select-none transition-all text-left', cargaMasivaAbierta ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800 text-slate-900 dark:text-white font-bold shadow-xs' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700']"
    >
      <span class="text-[11px] font-black uppercase tracking-wider">Carga Masiva de Archivos</span>
      <span class="text-[10px] font-mono">
        {{ cargaMasivaAbierta ? '◀' : '▶' }}
      </span>
    </div>
  </div>

  <div class="flex-1 divide-y divide-slate-100 dark:divide-slate-700 overflow-y-auto relative z-10">
    <div
      v-for="contacto in contactosRenderizados" :key="contacto.idUnico" @click="emit('seleccionar', contacto)"
      :class="['p-3.5 cursor-pointer transition-all border-l-4 relative', (modoVista === 'particular' && contactoSeleccionado?.idUnico === contacto.idUnico) ? 'bg-blue-50/50 dark:bg-blue-950/30 border-pink-500' : 'border-transparent hover:bg-slate-50/80 dark:hover:bg-slate-700/60']"
    >
      <div class="flex justify-between items-start gap-2">
        <div class="min-w-0">
          <h4 class="font-black text-xs text-heading truncate tracking-tight">{{ contacto.nombreCompleto }}</h4>
          <div class="flex items-center gap-1.5 mt-1">
            <span class="text-[10px] text-muted font-medium tracking-wide">{{ contacto.campana }}</span>
            <span v-if="contacto.estadoLead === 'Prospecto'" class="text-[9px] bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 px-1.5 py-px rounded font-black uppercase tracking-tight">
              {{ contacto.estadoLead }}
            </span>
          </div>
        </div>
        <span class="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 rounded text-[9px] font-black uppercase shrink-0 tracking-wider">
          {{ contacto.rol }}
        </span>
      </div>
    </div>
  </div>

 <Teleport to="body">
  <div
    v-if="cargaMasivaAbierta"
    class="panel-carga-flotante fixed z-[99999] surface-card rounded-xl shadow-2xl p-3 w-[295px] space-y-2 text-left animate-in fade-in slide-in-from-left-2 duration-150"
    :style="{ top: `${cargaTop}px`, left: `${cargaLeft}px` }"
  >
    <div class="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-slate-700 mb-1">
      <span class="text-[10px] font-black text-muted uppercase tracking-wider">Opciones de Importación</span>
      <button @click="cargaMasivaAbierta = false" class="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 text-xs font-black px-1 rounded cursor-pointer">✕</button>
    </div>

    <div class="border border-slate-200/70 dark:border-slate-700 rounded-xl p-2.5 bg-white dark:bg-slate-800">
      <div class="flex justify-between items-center mb-1.5">
        <span class="text-xs font-black text-body">Titulares</span>
        <button @click="seccionActiva = seccionActiva === 'titulares' ? null : 'titulares'" class="text-[10px] text-slate-900 dark:text-white font-bold">
          {{ seccionActiva === 'titulares' ? 'Ocultar' : 'Configurar' }}
        </button>
      </div>
      <div v-if="seccionActiva === 'titulares'" class="space-y-2 pt-1">
        <div class="flex items-center justify-between gap-1.5 bg-slate-50 dark:bg-slate-900 p-1.5 rounded-lg border border-slate-100 dark:border-slate-700">
          <span class="text-[10px] text-subtle font-bold">Acción inicial:</span>
          <select v-model="accionTitularesUnicos" class="bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-[11px] font-bold rounded-md border border-slate-200 dark:border-slate-600 px-2 py-0.5 focus:outline-none">
            <option value="Activar">Activar</option>
            <option value="Desactivar">Desactivar</option>
          </select>
        </div>
        <label class="w-full flex items-center justify-center bg-[#00965e] hover:bg-[#008252] text-white font-black text-[10px] py-2 px-3 rounded-lg cursor-pointer text-center shadow-xs">
          SUBIR ARCHIVO XLSX
          <input type="file" accept=".xlsx, .xls" class="hidden" @change="manejarArchivo($event, 'titulares')" />
        </label>
        <button type="button" @click="emit('descargarPlantilla', 'titulares')" class="w-full bg-[#f0f4f9] dark:bg-slate-700 hover:bg-[#e4eafd] dark:hover:bg-slate-600 text-slate-900 dark:text-white font-black text-[10px] py-2 px-3 rounded-lg border border-slate-100 dark:border-slate-600 text-center">
          DESCARGAR PLANTILLA BASE
        </button>
      </div>
    </div>

    <div class="border border-slate-200/70 dark:border-slate-700 rounded-xl p-2.5 bg-white dark:bg-slate-800">
      <div class="flex justify-between items-center mb-1.5">
        <span class="text-xs font-black text-body">Beneficiarios</span>
        <button @click="seccionActiva = seccionActiva === 'beneficiarios' ? null : 'beneficiarios'" class="text-[10px] text-slate-900 dark:text-white font-bold">
          {{ seccionActiva === 'beneficiarios' ? 'Ocultar' : 'Configurar' }}
        </button>
      </div>
      <div v-if="seccionActiva === 'beneficiarios'" class="space-y-2 pt-1">
        <div class="flex items-center justify-between gap-1.5 bg-slate-50 dark:bg-slate-900 p-1.5 rounded-lg border border-slate-100 dark:border-slate-700">
          <span class="text-[10px] text-subtle font-bold">Acción:</span>
          <select v-model="accionDocumento" class="bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-[11px] font-bold rounded-md border border-slate-200 dark:border-slate-600 px-2 py-0.5 focus:outline-none">
            <option value="Activar">Activar</option>
            <option value="Desactivar">Desactivar</option>
          </select>
        </div>
        <label class="w-full flex items-center justify-center bg-[#00965e] hover:bg-[#008252] text-white font-black text-[10px] py-2 px-3 rounded-lg cursor-pointer text-center shadow-xs">
          SUBIR ARCHIVO XLSX
          <input type="file" accept=".xlsx, .xls" class="hidden" @change="manejarArchivo($event, 'beneficiarios')" />
        </label>
        <button type="button" @click="emit('descargarPlantilla', 'beneficiarios')" class="w-full bg-[#f0f4f9] dark:bg-slate-700 hover:bg-[#e4eafd] dark:hover:bg-slate-600 text-slate-900 dark:text-white font-black text-[10px] py-2 px-3 rounded-lg border border-slate-100 dark:border-slate-600 text-center">
          DESCARGAR PLANTILLA BASE
        </button>
      </div>
    </div>

    <div class="border border-slate-200/70 dark:border-slate-700 rounded-xl p-2.5 bg-white dark:bg-slate-800">
      <div class="flex justify-between items-center mb-1.5">
        <span class="text-xs font-black text-body">Inscripción</span>
        <button @click="seccionActiva = seccionActiva === 'inscripcion' ? null : 'inscripcion'" class="text-[10px] text-slate-900 dark:text-white font-bold">
          {{ seccionActiva === 'inscripcion' ? 'Ocultar' : 'Configurar' }}
        </button>
      </div>

      <div v-if="seccionActiva === 'inscripcion'" class="space-y-2 pt-1">


        <div class="flex items-center justify-between gap-1.5 bg-slate-50 dark:bg-slate-900 p-1.5 rounded-lg border border-slate-100 dark:border-slate-700">
          <div class="flex flex-col">
            <span class="text-[10px] text-body font-black">Cupos por Inscripción:</span>
            <span class="text-[8px] text-muted font-medium">Límite permitido por archivo</span>
          </div>
          <select v-model="maxPersonasInscripcion" class="bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-[11px] font-bold rounded-md border border-slate-200 dark:border-slate-600 px-2 py-0.5 focus:outline-none">
            <option :value="1">1 Persona</option>
            <option :value="2">2 Personas</option>
            <option :value="3">3 Personas</option>
            <option :value="4">4 Personas</option>
            <option :value="5">5 Personas (Máx)</option>
          </select>
        </div>

        <label class="w-full flex items-center justify-center bg-[#00965e] hover:bg-[#008252] text-white font-black text-[10px] py-2 px-3 rounded-lg cursor-pointer text-center shadow-xs">
          SUBIR ARCHIVO XLSX
          <input type="file" accept=".xlsx, .xls" class="hidden" @change="manejarArchivo($event, 'inscripcion')" />
        </label>

        <button type="button" @click="emit('descargarPlantilla', 'inscripcion')" class="w-full bg-[#f0f4f9] dark:bg-slate-700 hover:bg-[#e4eafd] dark:hover:bg-slate-600 text-slate-900 dark:text-white font-black text-[10px] py-2 px-3 rounded-lg border border-slate-100 dark:border-slate-600 text-center">
          DESCARGAR PLANTILLA BASE
        </button>
      </div>
    </div>

    <div class="border border-slate-200/70 dark:border-slate-700 rounded-xl p-2.5 bg-white dark:bg-slate-800">
      <div class="flex justify-between items-center mb-1.5">
        <span class="text-xs font-black text-body">Remplazo</span>
        <button @click="seccionActiva = seccionActiva === 'remplazo' ? null : 'remplazo'" class="text-[10px] text-slate-900 dark:text-white font-bold">
          {{ seccionActiva === 'remplazo' ? 'Ocultar' : 'Configurar' }}
        </button>
      </div>
      <div v-if="seccionActiva === 'remplazo'" class="pt-1 space-y-2">
        <label class="w-full flex items-center justify-center bg-[#00965e] hover:bg-[#008252] text-white font-black text-[10px] py-2 px-3 rounded-lg cursor-pointer text-center shadow-xs">
          SUBIR ARCHIVO XLSX
          <input type="file" accept=".xlsx, .xls" class="hidden" @change="manejarArchivo($event, 'remplazo')" />
        </label>
      </div>
    </div>
  </div>

  <div
    v-if="filtrosAbiertos"
    class="panel-flotante-root fixed z-[99999] surface-card rounded-xl shadow-2xl p-2 w-[210px] text-left animate-in fade-in slide-in-from-left-2 duration-150 space-y-0.5"
    :style="{ top: `${menuTop}px`, left: `${menuLeft}px` }"
  >
    <div class="px-2 py-1.5 border-b border-slate-100 dark:border-slate-700 mb-1 flex justify-between items-center">
      <span class="text-[9px] font-black uppercase text-muted tracking-wider">Filtros Avanzados</span>
      <button @click="filtrosAbiertos = false; subMenuActivo = null" class="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 text-xs font-black">✕</button>
    </div>

    <button
      @click="abrirSubMenu($event, 'rol')"
      :class="[
        'w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-bold flex justify-between items-center transition-all cursor-pointer',
        subMenuActivo === 'rol' ? 'bg-blue-600 text-white shadow-sm font-extrabold' : 'text-body hover:bg-slate-100 dark:hover:bg-slate-700',
        filtroRolLocal !== 'todos' && subMenuActivo !== 'rol' ? 'bg-blue-50 dark:bg-blue-950/40 text-slate-900 dark:text-white font-bold border border-blue-100/50 dark:border-blue-800/50' : ''
      ]"
    >
      <span class="truncate">{{ textoRolActivo }}</span>
      <span class="text-[9px] font-mono opacity-50" :class="{ 'text-white/80': subMenuActivo === 'rol' }">▶</span>
    </button>

    <button
      @click="abrirSubMenu($event, 'estado')"
      :class="[
        'w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-bold flex justify-between items-center transition-all cursor-pointer',
        subMenuActivo === 'estado' ? 'bg-blue-600 text-white shadow-sm font-extrabold' : 'text-body hover:bg-slate-100 dark:hover:bg-slate-700',
        filtroEstadoLocal !== 'todos' && subMenuActivo !== 'estado' ? 'bg-blue-50 dark:bg-blue-950/40 text-slate-900 dark:text-white font-bold border border-blue-100/50 dark:border-blue-800/50' : ''
      ]"
    >
      <span class="truncate">{{ textoEstadoActivo }}</span>
      <span class="text-[9px] font-mono opacity-50" :class="{ 'text-white/80': subMenuActivo === 'estado' }">▶</span>
    </button>

    <button
      @click="abrirSubMenu($event, 'origen')"
      :class="[
        'w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-bold flex justify-between items-center transition-all cursor-pointer',
        subMenuActivo === 'origen' ? 'bg-blue-600 text-white shadow-sm font-extrabold' : 'text-body hover:bg-slate-100 dark:hover:bg-slate-700',
        filtroOrigenLocal !== 'todos' && subMenuActivo !== 'origen' ? 'bg-blue-50 dark:bg-blue-950/40 text-slate-900 dark:text-white font-bold border border-blue-100/50 dark:border-blue-800/50' : ''
      ]"
    >
      <span class="truncate">{{ textoOrigenActivo }}</span>
      <span class="text-[9px] font-mono opacity-50" :class="{ 'text-white/80': subMenuActivo === 'origen' }">▶</span>
    </button>

    <button
      @click="abrirSubMenu($event, 'campana')"
      :class="[
        'w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-bold flex justify-between items-center transition-all cursor-pointer',
        subMenuActivo === 'campana' ? 'bg-blue-600 text-white shadow-sm font-extrabold' : 'text-body hover:bg-slate-100 dark:hover:bg-slate-700',
        filtroCampanaLocal !== 'todos' && subMenuActivo !== 'campana' ? 'bg-blue-50 dark:bg-blue-950/40 text-slate-900 dark:text-white font-bold border border-blue-100/50 dark:border-blue-800/50' : ''
      ]"
    >
      <span class="truncate">{{ textoCampanaActiva }}</span>
      <span class="text-[9px] font-mono opacity-50" :class="{ 'text-white/80': subMenuActivo === 'campana' }">▶</span>
    </button>

    <button
      @click="abrirSubMenu($event, 'edad')"
      :class="[
        'w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-bold flex justify-between items-center transition-all cursor-pointer',
        subMenuActivo === 'edad' ? 'bg-blue-600 text-white shadow-sm font-extrabold' : 'text-body hover:bg-slate-100 dark:hover:bg-slate-700',
        filtroEdadLocal !== 'todos' && subMenuActivo !== 'edad' ? 'bg-blue-50 dark:bg-blue-950/40 text-slate-900 dark:text-white font-bold border border-blue-100/50 dark:border-blue-800/50' : ''
      ]"
    >
      <span class="truncate">{{ textoEdadActiva }}</span>
      <span class="text-[9px] font-mono opacity-50" :class="{ 'text-white/80': subMenuActivo === 'edad' }">▶</span>
    </button>
  </div>

  <div
    v-if="filtrosAbiertos && subMenuActivo"
    class="panel-sub-flotante fixed z-[100000] surface-card rounded-xl shadow-2xl p-1 w-[180px] text-left animate-in fade-in slide-in-from-left-1 duration-100 space-y-px"
    :style="{ top: `${subMenuTop}px`, left: `${subMenuLeft}px` }"
  >
    <template v-if="subMenuActivo === 'rol'">
      <button @click="filtroRolLocal = 'todos'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroRolLocal === 'todos' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Todos los Roles</button>
      <button @click="filtroRolLocal = 'titular'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroRolLocal === 'titular' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Titulares</button>
      <button @click="filtroRolLocal = 'beneficiario'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroRolLocal === 'beneficiario' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Beneficiarios</button>
    </template>

    <template v-if="subMenuActivo === 'estado'">
      <button @click="filtroEstadoLocal = 'todos'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroEstadoLocal === 'todos' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Todos los Estados</button>
      <button @click="filtroEstadoLocal = 'Prospecto'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroEstadoLocal === 'Prospecto' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Solo Prospectos</button>
      <button @click="filtroEstadoLocal = 'Cliente'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroEstadoLocal === 'Cliente' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Solo Clientes</button>
    </template>

    <template v-if="subMenuActivo === 'origen'">
      <button @click="filtroOrigenLocal = 'todos'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroOrigenLocal === 'todos' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Todos los Orígenes</button>
      <button @click="filtroOrigenLocal = 'Llamada Directa'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroOrigenLocal === 'Llamada Directa' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Llamada Directa</button>
      <button @click="filtroOrigenLocal = 'Formulario Web'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroOrigenLocal === 'Formulario Web' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Formulario Web</button>
      <button @click="filtroOrigenLocal = 'WhatsApp'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroOrigenLocal === 'WhatsApp' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">WhatsApp</button>
    </template>

    <template v-if="subMenuActivo === 'campana'">
      <button @click="filtroCampanaLocal = 'todos'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroCampanaLocal === 'todos' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Todas las Campañas</button>
      <button @click="filtroCampanaLocal = 'Registro Manual'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroCampanaLocal === 'Registro Manual' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Registro Manual</button>
      <button @click="filtroCampanaLocal = 'Campaña Black Friday'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroCampanaLocal === 'Campaña Black Friday' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Black Friday</button>
      <button @click="filtroCampanaLocal = 'Inscripción Orgánica'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroCampanaLocal === 'Inscripción Orgánica' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Inscripción Orgánica</button>
    </template>

    <template v-if="subMenuActivo === 'edad'">
      <button @click="filtroEdadLocal = 'todos'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroEdadLocal === 'todos' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Todas las Edades</button>
      <button @click="filtroEdadLocal = 'menores'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroEdadLocal === 'menores' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Menores (&lt; 18)</button>
      <button @click="filtroEdadLocal = 'adultos'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroEdadLocal === 'adultos' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Adultos (18 - 60)</button>
      <button @click="filtroEdadLocal = 'mayores'; subMenuActivo = null" :class="['w-full text-left px-2.5 py-1.5 text-[11px] rounded-md transition-all font-medium cursor-pointer', filtroEdadLocal === 'mayores' ? 'bg-blue-600 text-white font-bold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700']">Adultos Mayores (&gt; 60)</button>
    </template>
  </div>

  <div v-if="confirmarDesactivarAbierto" class="fixed inset-0 z-[999999] bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="surface-card rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 duration-150">
      <div class="p-5 text-center">
        <div class="w-11 h-11 rounded-2xl bg-amber-50 dark:bg-amber-950/40 flex items-center justify-center mx-auto mb-3 text-lg">⚠️</div>
        <h3 class="text-xs font-black uppercase tracking-wider text-body mb-1">Confirmar desactivación masiva</h3>
        <p class="text-[11px] text-subtle">
          Vas a <strong>desactivar</strong> los registros del archivo
          <strong>"{{ cargaPendiente?.archivo.name }}"</strong> en la sección de {{ cargaPendiente?.seccion === 'titulares' ? 'titulares' : 'beneficiarios' }}. ¿Deseas continuar?
        </p>
      </div>
      <div class="flex gap-2 px-5 pb-5">
        <button @click="cancelarCargaDesactivar" class="flex-1 py-2 text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 bg-white dark:bg-slate-800 border border-default rounded-lg cursor-pointer">Cancelar</button>
        <button @click="confirmarCargaDesactivar" class="flex-1 py-2 text-xs font-black text-white bg-amber-600 hover:bg-amber-700 rounded-lg cursor-pointer shadow-sm">Desactivar</button>
      </div>
    </div>
  </div>

  <div v-if="modalAgregarAbierto" class="fixed inset-0 z-[999999] bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="surface-card rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-150">
      <div class="px-4 py-3 surface-header border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
        <h3 class="text-xs font-black uppercase tracking-wider text-body">Crear Registro Manual</h3>
        <button @click="cerrarModalProspecto" class="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 text-sm font-black cursor-pointer">✕</button>
      </div>

      <div class="p-4 space-y-3 text-left">
        <div>
          <label class="block text-[10px] font-black uppercase tracking-wide text-muted mb-1">Nombre Completo *</label>
          <input v-model="nuevoProspecto.nombreCompleto" type="text" placeholder="Ej: Juan Pérez" class="w-full input-surface rounded-lg px-3 py-2 text-xs focus:outline-none focus:bg-white dark:focus:bg-slate-800 focus:ring-1 focus:ring-blue-600" />
        </div>
        <div class="grid grid-cols-3 gap-2">
          <div class="col-span-1">
            <label class="block text-[10px] font-black uppercase tracking-wide text-muted mb-1">Tipo Doc.</label>
            <select v-model="nuevoProspecto.tipoDocumento" class="w-full input-surface rounded-lg px-2 py-2 text-xs focus:outline-none focus:bg-white dark:focus:bg-slate-800">
              <option value="CC">CC</option>
              <option value="TI">TI</option>
              <option value="CE">CE</option>
              <option value="PAS">PAS</option>
            </select>
          </div>
          <div class="col-span-2">
            <label class="block text-[10px] font-black uppercase tracking-wide text-muted mb-1">Número Documento *</label>
            <input v-model="nuevoProspecto.documento" type="text" placeholder="Ej: 1020340" class="w-full input-surface rounded-lg px-3 py-2 text-xs focus:outline-none focus:bg-white dark:focus:bg-slate-800 focus:ring-1 focus:ring-blue-600" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-[10px] font-black uppercase tracking-wide text-muted mb-1">Teléfono</label>
            <input v-model="nuevoProspecto.telefono" type="text" placeholder="Ej: 300123" class="w-full input-surface rounded-lg px-3 py-2 text-xs focus:outline-none focus:bg-white dark:focus:bg-slate-800" />
          </div>
          <div>
            <label class="block text-[10px] font-black uppercase tracking-wide text-muted mb-1">Email</label>
            <input v-model="nuevoProspecto.email" type="email" placeholder="correo@ejemplo.com" class="w-full input-surface rounded-lg px-3 py-2 text-xs focus:outline-none focus:bg-white dark:focus:bg-slate-800" />
          </div>
        </div>
      </div>

      <div class="px-4 py-3 surface-header border-t border-slate-100 dark:border-slate-700 flex justify-end gap-2">
        <button @click="cerrarModalProspecto" class="px-3 py-2 text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 bg-white dark:bg-slate-800 border border-default rounded-lg cursor-pointer">Cancelar</button>
        <button @click="procesarGuardado" class="px-4 py-2 text-xs font-black text-white bg-blue-600 hover:bg-blue-700 rounded-lg cursor-pointer shadow-sm">Guardar Registro</button>
      </div>
    </div>
  </div>
 </Teleport>
</template>