<script setup lang="ts">
import { ref, computed } from 'vue'

// --- INTERFACES DE MODELO ---
interface ServicioParticular { 
  nombre: string; 
  fecha: string; 
  estado: 'Activo' | 'Terminado'; 
}

interface Beneficiario { 
  nombreCompleto: string; 
  tipoDocumento: string; 
  documento: string; 
  edad: number; 
  genero: string; 
  telefono?: string; 
  parentesco: string; 
}

interface Contacto { 
  idUnico: string; 
  nombre: string;
  apellidos: string;
  nombreCompleto: string; 
  rol: 'titular' | 'beneficiario'; 
  tipoDocumento: string; 
  documento: string; 
  telefono: string; 
  whatsapp: string; 
  email: string; 
  empresaAsociada?: string;
  categoria?: string;
  ocupacion?: string;
  cargo?: string;
  fechaNacimiento?: string;
  ciudad: string; 
  pais: string; 
  estado: string; // Estado de gestión del contacto
  etiquetas?: string[];
  canalOrigen: string; 
  campana: string; 
  estadoLead: string; 
  ultimoContacto: string; 
  proximoContacto: string; 
  cantidadLlamadas: number; 
  cantidadEmails: number; 
  cantidadInteraccionesRedes?: { instagram?: number; facebook?: number; linkedin?: number; whatsapp?: number };
  notes?: string; // Historial de notas principal
  historialNotas?: Array<{ fecha: string; autor: string; texto: string }>; // Listado de notas
  edad: number; 
  genero: string; 
  serviciosHistoricos: ServicioParticular[]; 
  beneficiariosAsociados?: Beneficiario[]; 
  bitacora?: any[]; 
}

// --- PROPS & EMITS ---
const props = defineProps<{
  contacto: Contacto
}>()

const emit = defineEmits<{
  (e: 'abrir-modal-beneficiario'): void
}>()

// --- CONTROL DE PESTAÑAS ---
type TabActiva = 'datos' | 'servicios'
const pestañaActiva = ref<TabActiva>('datos')

// --- FILTRADO DE SERVICIOS ---
const filtroNombre = ref('')
const fechaDesde = ref('')
const fechaHasta = ref('')

const serviciosHistoricosFiltrados = computed(() => {
  let servicios = props.contacto.serviciosHistoricos || []
  const queryNombre = filtroNombre.value.trim().toLowerCase()
  if (queryNombre) {
    servicios = servicios.filter(serv => serv.nombre.toLowerCase().includes(queryNombre))
  }
  if (fechaDesde.value || fechaHasta.value) {
    servicios = servicios.filter(serv => {
      const fechaServicio = new Date(serv.fecha).getTime()
      if (isNaN(fechaServicio)) return true 
      const desde = fechaDesde.value ? new Date(fechaDesde.value).getTime() : null
      const hasta = fechaHasta.value ? new Date(fechaHasta.value).getTime() : null
      if (desde && fechaServicio < desde) return false
      if (hasta && fechaServicio > hasta) return false
      return true
    })
  }
  return servicios
})

const limpiarFiltros = () => {
  filtroNombre.value = ''
  fechaDesde.value = ''
  fechaHasta.value = ''
}

// --- MÉTRICAS Y TOP SERVICIOS ---
const totalServicios = computed(() => props.contacto.serviciosHistoricos?.length || 0)
const serviciosActivosContador = computed(() => props.contacto.serviciosHistoricos?.filter(s => s.estado === 'Activo').length || 0)

const serviciosMasUsados = computed(() => {
  const servicios = props.contacto.serviciosHistoricos || []
  const mapeoFrecuencia: Record<string, number> = {}
  servicios.forEach(s => { mapeoFrecuencia[s.nombre] = (mapeoFrecuencia[s.nombre] || 0) + 1 })
  
  const conteos = Object.values(mapeoFrecuencia)
  const maximoConteo = conteos.length > 0 ? Math.max(...conteos) : 1

  const coloresBarras = [
    'from-blue-600 to-indigo-600 shadow-blue-100',
    'from-sky-500 to-blue-500 shadow-sky-100',
    'from-slate-500 to-slate-600 shadow-slate-100'
  ]

  return Object.entries(mapeoFrecuencia)
    .map(([nombre, cantidad], index) => ({
      nombre,
      cantidad,
      porcentaje: `${(cantidad / maximoConteo) * 100}%`,
      colorClass: coloresBarras[index] || 'from-slate-500 to-slate-600'
    }))
    .sort((a, b) => b.cantidad - a.cantidad)
    .slice(0, 3) 
})

// --- MÉTRICAS DE REDES ---
const metricasRedes = computed(() => {
  const whatsappInt = props.contacto.cantidadInteraccionesRedes?.whatsapp ?? 32
  const instagramInt = props.contacto.cantidadInteraccionesRedes?.instagram ?? 14
  const correoInt = props.contacto.cantidadEmails ?? 12
  const facebookInt = props.contacto.cantidadInteraccionesRedes?.facebook ?? 16

  const lista = [
    { nombre: 'WhatsApp', cantidad: whatsappInt, color: 'bg-emerald-500', porcentaje: '50%' },
    { nombre: 'Instagram', cantidad: instagramInt, color: 'bg-sky-500', porcentaje: '25%' },
    { nombre: 'Correo', cantidad: correoInt, color: 'bg-amber-500', porcentaje: '20%' },
    { nombre: 'Facebook', cantidad: facebookInt, color: 'bg-blue-600', porcentaje: '15%' }
  ]

  return lista.sort((x: { cantidad: number }, y: { cantidad: number }) => Number(y.cantidad) - Number(x.cantidad))
})
</script>

<template>
  <div class="flex-1 flex flex-col bg-white dark:bg-slate-800 p-6 h-full max-h-full overflow-hidden select-none">

    <div class="pb-4 border-b border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
      <div>
        <span class="text-[9px] bg-blue-50 dark:bg-blue-950/50 text-slate-900 dark:text-white border border-blue-200 dark:border-blue-800 font-black px-2 py-0.5 rounded uppercase tracking-wider inline-block">
          {{ contacto.estadoLead }}
        </span>
        <h2 class="text-xl font-black text-slate-900 dark:text-slate-100 tracking-tight mt-1">
          {{ contacto.nombreCompleto || `${contacto.nombre} ${contacto.apellidos}` }}
        </h2>
      </div>

      <div class="bg-slate-100 dark:bg-slate-900 p-1 rounded-full inline-flex items-center gap-1 self-start sm:self-center border border-slate-200/60 dark:border-slate-700/60">
        <button
          @click="pestañaActiva = 'datos'"
          :class="[
            'px-4 py-1.5 rounded-full text-[10px] font-black tracking-widest uppercase transition-all duration-200 cursor-pointer',
            pestañaActiva === 'datos' ? 'bg-white dark:bg-slate-700 text-slate-900 font-bold dark:text-white shadow-xs' : 'text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300'
          ]"
        >
          Datos Personales
        </button>
        <button
          @click="pestañaActiva = 'servicios'"
          :class="[
            'px-4 py-1.5 rounded-full text-[10px] font-black tracking-widest uppercase transition-all duration-200 cursor-pointer',
            pestañaActiva === 'servicios' ? 'bg-white dark:bg-slate-700 text-slate-900 font-bold dark:text-white shadow-xs' : 'text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300'
          ]"
        >
          Servicios
        </button>
      </div>
    </div>

    <div class="flex-1 mt-5 min-h-0 overflow-hidden">
      
      <div v-if="pestañaActiva === 'datos'" class="grid grid-cols-1 md:grid-cols-12 gap-5 h-full overflow-y-auto pr-1 custom-scrollbar animate-fadeIn items-start">
        
        <div class="md:col-span-7 space-y-4">
          
          <div>
            <h3 class="text-[9px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest mb-2 pb-1 border-b border-slate-100 dark:border-slate-700">
              Identificación Básica
            </h3>
            <div class="bg-slate-50/60 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-700/60 rounded-xl p-3 text-xs grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div class="flex justify-between items-center border-b border-slate-100/60 dark:border-slate-700/60 sm:border-0 pb-1 sm:pb-0"><span class="text-slate-400 dark:text-slate-500 font-bold">Nombre:</span><strong class="text-slate-800 dark:text-slate-200">{{ contacto.nombre }}</strong></div>
              <div class="flex justify-between items-center border-b border-slate-100/60 dark:border-slate-700/60 sm:border-0 pb-1 sm:pb-0"><span class="text-slate-400 dark:text-slate-500 font-bold">Apellidos:</span><strong class="text-slate-800 dark:text-slate-200">{{ contacto.apellidos }}</strong></div>
              <div class="flex justify-between items-center sm:col-span-2"><span class="text-slate-400 dark:text-slate-500 font-bold">Categoría:</span><strong class="text-slate-900 dark:text-white bg-blue-50/60 dark:bg-blue-950/40 px-2 py-0.5 rounded font-black text-[10px] uppercase">{{ contacto.categoria || 'Sin Categoría' }}</strong></div>
            </div>
          </div>

          <div>
            <h3 class="text-[9px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest mb-2 pb-1 border-b border-slate-100 dark:border-slate-700">
              Canales Directos de Comunicación
            </h3>
            <div class="bg-slate-50/60 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-700/60 rounded-xl p-3 text-xs space-y-2.5">
              <div class="flex justify-between items-center"><span class="text-slate-400 dark:text-slate-500 font-bold">Teléfono:</span><strong class="text-slate-800 dark:text-slate-200 font-mono text-[11px]">{{ contacto.telefono }}</strong></div>
              <div class="flex justify-between items-center"><span class="text-slate-400 dark:text-slate-500 font-bold">WhatsApp Corp:</span><strong class="text-emerald-600 dark:text-emerald-400 font-mono text-[11px]">➔ {{ contacto.whatsapp }}</strong></div>
              <div class="flex justify-between items-center"><span class="text-slate-400 dark:text-slate-500 font-bold">Email Asociado:</span><strong class="text-slate-800 dark:text-slate-200 truncate max-w-[240px]">{{ contacto.email }}</strong></div>
            </div>
          </div>

          <div>
            <h3 class="text-[9px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest mb-2 pb-1 border-b border-slate-100 dark:border-slate-700">
              Entorno Profesional y Corporativo
            </h3>
            <div class="bg-slate-50/60 dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-700/60 rounded-xl p-3 text-xs grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div class="flex justify-between items-center"><span class="text-slate-400 dark:text-slate-500 font-bold">Empresa:</span><strong class="text-slate-800 dark:text-slate-200 truncate max-w-[140px]">{{ contacto.empresaAsociada || 'N/A' }}</strong></div>
              <div class="flex justify-between items-center"><span class="text-slate-400 dark:text-slate-500 font-bold">Ocupación:</span><strong class="text-slate-800 dark:text-slate-200 truncate max-w-[140px]">{{ contacto.ocupacion || 'N/A' }}</strong></div>
              <div class="flex justify-between items-center sm:col-span-2 border-t border-slate-100/60 dark:border-slate-700/60 pt-2"><span class="text-slate-400 dark:text-slate-500 font-bold">Cargo:</span><strong class="text-slate-800 dark:text-slate-200">{{ contacto.cargo || 'No Definido' }}</strong></div>
            </div>
          </div>

          <div>
            <h3 class="text-[9px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest mb-2 pb-1 border-b border-slate-100 dark:border-slate-700">
              Información Sociodemográfica y Legal
            </h3>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="bg-slate-50/40 dark:bg-slate-900/30 p-2.5 rounded-xl border border-slate-200/40 dark:border-slate-700/40"><span class="text-slate-400 dark:text-slate-500 block text-[8px] uppercase tracking-wide">Género / Edad</span><strong class="text-slate-800 dark:text-slate-200 text-[11px] font-bold">{{ contacto.genero }}, {{ contacto.edad }} años</strong></div>
              <div class="bg-slate-50/40 dark:bg-slate-900/30 p-2.5 rounded-xl border border-slate-200/40 dark:border-slate-700/40"><span class="text-slate-400 dark:text-slate-500 block text-[8px] uppercase tracking-wide">F. Nacimiento</span><strong class="text-slate-800 dark:text-slate-200 text-[11px] font-mono font-bold">{{ contacto.fechaNacimiento || 'N/A' }}</strong></div>
              <div class="bg-slate-50/40 dark:bg-slate-900/30 p-2.5 rounded-xl border border-slate-200/40 dark:border-slate-700/40 col-span-2"><span class="text-slate-400 dark:text-slate-500 block text-[8px] uppercase tracking-wide">Ubicación Registrada</span><strong class="text-slate-800 dark:text-slate-200 text-[11px] font-bold">{{ contacto.ciudad }}, {{ contacto.pais }}</strong></div>
            </div>
          </div>

        </div>

        <div class="md:col-span-5 space-y-4">
          
          <div class="border border-slate-200/80 dark:border-slate-700/80 rounded-2xl bg-white dark:bg-slate-800 p-4 shadow-2xs">
            <div class="pb-2 border-b border-slate-100 dark:border-slate-700 mb-3">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest block">Estado del Registro</span>
                <span class="text-[9px] bg-slate-900 dark:bg-slate-950 text-white font-mono font-black px-2 py-0.5 rounded uppercase tracking-wider">
                  {{ contacto.estado || 'Activo' }}
                </span>
              </div>
            </div>

            <div>
              <span class="text-[8px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider block mb-2">Etiquetas de Segmentación</span>
              <div class="flex flex-wrap gap-1.5" v-if="contacto.etiquetas && contacto.etiquetas.length">
                <span
                  v-for="(tag, i) in contacto.etiquetas"
                  :key="i"
                  class="bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-tight"
                >
                  #{{ tag }}
                </span>
              </div>
              <span v-else class="text-[10px] text-slate-400 dark:text-slate-500 italic">Sin etiquetas asignadas.</span>
            </div>
          </div>

          <div class="border border-slate-200/80 dark:border-slate-700/80 rounded-2xl bg-white dark:bg-slate-800 p-4 shadow-2xs">
            <h3 class="text-[10px] font-black uppercase text-slate-500 dark:text-slate-400 tracking-widest pb-1.5 border-b border-slate-100 dark:border-slate-700 mb-3">
              📝 Historial de Notas y Observaciones
            </h3>

            <div class="space-y-3 max-h-[220px] overflow-y-auto pr-1 custom-scrollbar">

              <div v-if="contacto.notes" class="bg-amber-50/50 dark:bg-amber-950/30 border border-amber-200/40 dark:border-amber-800/40 rounded-xl p-2.5 text-xs text-slate-700 dark:text-slate-300 leading-normal">
                <div class="flex justify-between items-center text-[8px] text-amber-700 dark:text-amber-400 font-black uppercase tracking-wider mb-1">
                  <span>Nota Principal</span>
                  <span>Sistema</span>
                </div>
                <p class="font-semibold">{{ contacto.notes }}</p>
              </div>

              <div
                v-for="(nota, idx) in contacto.historialNotas"
                :key="idx"
                class="bg-slate-50/80 dark:bg-slate-900/50 border border-slate-200/40 dark:border-slate-700/40 rounded-xl p-2.5 text-xs text-slate-700 dark:text-slate-300"
              >
                <div class="flex justify-between items-center text-[8px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-wider mb-1">
                  <span>{{ nota.fecha }}</span>
                  <span class="text-slate-900 font-bold dark:text-white">{{ nota.autor }}</span>
                </div>
                <p class="font-medium text-slate-600 dark:text-slate-400">{{ nota.texto }}</p>
              </div>

              <div v-if="!contacto.notes && (!contacto.historialNotas || !contacto.historialNotas.length)" class="text-center py-4 text-[10px] text-slate-400 dark:text-slate-500 italic">
                No hay notas registradas en el historial de este contacto.
              </div>

            </div>
          </div>

          <div class="border border-slate-200/60 dark:border-slate-700/60 rounded-2xl bg-slate-50/40 dark:bg-slate-900/30 p-3.5">
            <span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest block mb-2.5">Resumen de Interacciones</span>
            <div class="space-y-2">
              <div v-for="red in metricasRedes" :key="red.nombre" class="space-y-0.5">
                <div class="flex justify-between text-slate-600 dark:text-slate-400 items-center text-[10px]">
                  <span class="text-slate-800 dark:text-slate-200 font-bold">{{ red.nombre }}</span>
                  <span class="font-mono text-slate-400 dark:text-slate-500 font-bold">{{ red.cantidad }} int.</span>
                </div>
                <div class="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500" :class="red.color" :style="{ width: red.porcentaje }"></div>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>

      <div v-if="pestañaActiva === 'servicios'" class="flex flex-col h-full min-h-0 bg-slate-50/50 dark:bg-slate-900/30 border border-slate-200 dark:border-slate-700 rounded-2xl p-4 shadow-xs animate-fadeIn">

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 pb-4 border-b border-slate-200 dark:border-slate-700 shrink-0 items-stretch">

          <div class="lg:col-span-4 flex flex-col justify-between bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 p-3.5 rounded-xl shadow-xs">
            <div>
              <h3 class="text-sm font-black uppercase text-slate-900 dark:text-slate-100 tracking-tight">Historial de Catálogo</h3>
              <p class="text-[10px] text-slate-400 dark:text-slate-500 font-medium leading-tight mt-0.5">Métricas de recurrencia y control de contratos del cliente.</p>
            </div>

            <div class="flex items-center gap-2 font-mono text-[10px] mt-3 lg:mt-0">
              <span class="bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 px-2 py-0.5 rounded-lg font-black shadow-2xs">Activos: {{ serviciosActivosContador }}</span>
              <span class="bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600 px-2 py-0.5 rounded-lg font-black shadow-2xs">Total: {{ totalServicios }}</span>
            </div>
          </div>

          <div class="lg:col-span-8 bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 rounded-xl p-3.5 flex flex-col justify-center shadow-xs">
            <span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest block mb-2">📊 Top Servicios más contratados (Historial de uso)</span>

            <div v-if="serviciosMasUsados.length" class="space-y-2">
              <div v-for="item in serviciosMasUsados" :key="item.nombre" class="flex items-center gap-3">

                <div class="flex-1 bg-slate-100 dark:bg-slate-900 rounded-lg h-7 relative overflow-hidden border border-slate-200/40 dark:border-slate-700/40 shadow-inner">
                  <div
                    class="h-full bg-gradient-to-r flex items-center pl-3 transition-all duration-700 shadow-xs"
                    :class="item.colorClass"
                    :style="{ width: item.porcentaje }"
                  >
                    <span class="text-[10px] font-black text-white truncate drop-shadow-xs">
                      {{ item.nombre }}
                    </span>
                  </div>
                </div>

                <div class="shrink-0 font-mono text-[10px] font-black bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 h-7 px-2.5 flex items-center justify-center rounded-lg shadow-2xs">
                  {{ item.cantidad }} u.
                </div>

              </div>
            </div>
            <div v-else class="text-center py-4 text-[10px] text-slate-400 dark:text-slate-500 font-semibold">
              Sin datos de uso para calcular el top de servicios.
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-12 gap-2 my-3 shrink-0 items-end">
          <div class="sm:col-span-5">
            <span class="text-[8px] text-slate-400 dark:text-slate-500 font-black uppercase block mb-1 tracking-wider">Filtrar por Nombre</span>
            <input
              type="text"
              v-model="filtroNombre"
              placeholder="Escribe el nombre del servicio..."
              class="w-full bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 rounded-lg border border-slate-200 dark:border-slate-600 px-2.5 py-1 text-xs font-semibold focus:outline-none focus:border-blue-500 transition-all shadow-2xs"
            />
          </div>
          <div class="sm:col-span-3">
            <span class="text-[8px] text-slate-400 dark:text-slate-500 font-black uppercase block mb-1 tracking-wider">Desde</span>
            <input
              type="date"
              v-model="fechaDesde"
              class="w-full bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-lg border border-slate-200 dark:border-slate-600 px-2 py-0.5 text-[11px] font-mono focus:outline-none focus:border-blue-500 transition-all shadow-2xs"
            />
          </div>
          <div class="sm:col-span-3">
            <span class="text-[8px] text-slate-400 dark:text-slate-500 font-black uppercase block mb-1 tracking-wider">Hasta</span>
            <input
              type="date"
              v-model="fechaHasta"
              class="w-full bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-lg border border-slate-200 dark:border-slate-600 px-2 py-0.5 text-[11px] font-mono focus:outline-none focus:border-blue-500 transition-all shadow-2xs"
            />
          </div>
          <div class="sm:col-span-1 flex justify-end">
            <button
              @click="limpiarFiltros"
              title="Limpiar filtros"
              class="p-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 transition-all cursor-pointer shadow-2xs w-full text-center text-xs font-bold"
            >
              ✕
            </button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto min-h-0 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800 custom-scrollbar shadow-xs">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="bg-slate-50 dark:bg-slate-900 text-slate-400 dark:text-slate-500 font-black uppercase text-[8px] border-b border-slate-200 dark:border-slate-700 tracking-widest sticky top-0 z-10">
                <th class="p-3 pl-4">Detalle del Servicio</th>
                <th class="p-3">Fecha de Adquisición</th>
                <th class="p-3 text-right pr-4">Estado / Progreso</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-700 font-semibold text-slate-600 dark:text-slate-400">
              <tr v-for="(serv, idx) in serviciosHistoricosFiltrados" :key="idx" class="hover:bg-slate-50/40 dark:hover:bg-slate-700/40 transition-colors">
                <td class="p-3 pl-4">
                  <span class="font-extrabold text-slate-900 dark:text-slate-100 text-[11px] tracking-tight block truncate max-w-[300px]">
                    {{ serv.nombre }}
                  </span>
                </td>
                <td class="p-3 font-mono text-slate-500 dark:text-slate-400 text-[11px]">
                  {{ serv.fecha }}
                </td>
                <td class="p-3 text-right pr-4 whitespace-nowrap">
                  <span :class="[
                    'text-[7px] px-2 py-0.5 rounded font-black uppercase border tracking-wider inline-block mb-1',
                    serv.estado === 'Activo' ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800' : 'bg-slate-50 dark:bg-slate-900 text-slate-400 dark:text-slate-500 border-slate-200 dark:border-slate-600'
                  ]">
                    {{ serv.estado }}
                  </span>
                  <div class="w-20 ml-auto bg-slate-100 dark:bg-slate-700 rounded-full h-1">
                    <div class="h-1 rounded-full transition-all duration-300" :class="serv.estado === 'Activo' ? 'bg-emerald-500 w-full' : 'bg-slate-300 dark:bg-slate-600 w-1/3'"></div>
                  </div>
                </td>
              </tr>
              <tr v-if="serviciosHistoricosFiltrados.length === 0">
                <td colspan="3" class="text-center p-8 text-[10px] text-slate-400 dark:text-slate-500 font-bold bg-slate-50/20 dark:bg-slate-900/20">
                  Ningún servicio coincide con los parámetros aplicados.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>

    </div>
  </div>
</template>

<style scoped>
.animate-fadeIn { animation: fadeIn 0.15s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(2px); } to { opacity: 1; transform: translateY(0); } }

.custom-scrollbar::-webkit-scrollbar { width: 5px; height: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>