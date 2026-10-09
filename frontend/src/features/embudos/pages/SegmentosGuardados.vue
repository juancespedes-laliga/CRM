<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight, Bookmark, Mail, MessageCircle, ClipboardList, Users, Search, SlidersHorizontal, ArrowRight, Trash2, AlertTriangle } from 'lucide-vue-next'
import { type Segmento } from '../constants/segmentos.constants'
import { setSegmentoPreseleccionado } from '../composables/useSegmentoPreseleccionado'
import { useSegmentosGuardados } from '../composables/useSegmentosGuardados'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const router = useRouter()
const nf = new Intl.NumberFormat('es-CO')

const { segmentos: todos, eliminar } = useSegmentosGuardados()

/* ── Filtros de la lista de segmentos ────────────────────────────── */
const buscar = ref('')
const orden = ref<'tamano' | 'reciente' | 'nombre'>('tamano')
const minPersonas = ref('')
const soloAlcanzables = ref<'' | 'correo' | 'celular'>('')

const RANK_RECIENTE: Record<string, number> = { 'hoy': 0, 'hace 2 días': 2, 'hace 5 días': 5, 'hace 1 semana': 7 }

const segmentos = computed<Segmento[]>(() => {
  const q = buscar.value.toLowerCase().trim()
  let lista = todos.value.filter(s => {
    if (q && !(`${s.nombre} ${s.descripcion} ${s.criterios.join(' ')}`.toLowerCase().includes(q))) return false
    if (minPersonas.value && s.personas < +minPersonas.value) return false
    if (soloAlcanzables.value === 'correo' && s.conCorreo < s.personas * 0.6) return false
    if (soloAlcanzables.value === 'celular' && s.conCelular < s.personas * 0.6) return false
    return true
  })
  lista = [...lista].sort((a, b) => {
    if (orden.value === 'tamano') return b.personas - a.personas
    if (orden.value === 'nombre') return a.nombre.localeCompare(b.nombre)
    return (RANK_RECIENTE[a.actualizado] ?? 99) - (RANK_RECIENTE[b.actualizado] ?? 99)
  })
  return lista
})

/* ── Acciones ───────────────────────────────────────────────────── */
const aviso = ref('')
let t: ReturnType<typeof setTimeout> | undefined

// Confirmacion antes de enviar (correo/whatsapp/tarea).
const pendienteAccion = ref<{ s: Segmento; tipo: 'Correo' | 'WhatsApp' | 'Tarea' } | null>(null)
const pedirAccion = (s: Segmento, tipo: 'Correo' | 'WhatsApp' | 'Tarea') => {
  pendienteAccion.value = { s, tipo }
}
const mensajeAccion = computed(() => {
  if (!pendienteAccion.value) return ''
  const { s, tipo } = pendienteAccion.value
  const base = tipo === 'Correo' ? s.conCorreo : tipo === 'WhatsApp' ? s.conCelular : s.personas
  const accion = tipo === 'Tarea'
    ? `Se van a crear ${nf.format(base)} tareas para el segmento "${s.nombre}".`
    : `Se va a enviar ${tipo} a ${nf.format(base)} personas del segmento "${s.nombre}".`
  return `${accion} Esta acción todavía no está conectada a un proveedor/módulo real — es solo una vista previa. ¿Continuar?`
})
const confirmarAccion = () => {
  if (!pendienteAccion.value) return
  const { s, tipo } = pendienteAccion.value
  const base = tipo === 'Correo' ? s.conCorreo : tipo === 'WhatsApp' ? s.conCelular : s.personas
  aviso.value = tipo === 'Tarea'
    ? `Se crearían ${nf.format(base)} tareas para el segmento "${s.nombre}". (Vista previa: no se creó nada.)`
    : `Se enviaría ${tipo} a ${nf.format(base)} personas del segmento "${s.nombre}". (Vista previa: no se envió nada.)`
  clearTimeout(t)
  t = setTimeout(() => { aviso.value = '' }, 3500)
  pendienteAccion.value = null
}

// Confirmacion antes de eliminar un segmento guardado.
const pendienteEliminar = ref<Segmento | null>(null)
const confirmarEliminar = () => {
  if (!pendienteEliminar.value) return
  eliminar(pendienteEliminar.value.id)
  pendienteEliminar.value = null
}

const abrirEnSegmentador = (s: Segmento) => {
  setSegmentoPreseleccionado(s.filtros)
  router.push('/embudos/afiliado')
}
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div>
      <nav class="flex items-center gap-1.5 text-[12px] mb-1.5">
        <span class="text-slate-400 dark:text-slate-500">CRM Mercadeo</span>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <button class="text-slate-400 dark:text-slate-500 hover:text-[#2447F9] font-semibold transition-colors" @click="router.push('/embudos')">Embudos</button>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <span class="font-bold text-[#0F172A] dark:text-slate-100">Segmentos guardados</span>
      </nav>
      <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
        <Bookmark :size="18" class="text-[#C9A227]" /> Segmentos guardados
        <span class="bg-[#FEF9C3] dark:bg-amber-950/40 text-[#C9A227] dark:text-amber-300 text-[11px] font-bold px-2.5 py-0.5 rounded-full">{{ segmentos.length }}</span>
      </h2>
      <p class="text-[12px] text-body mt-0.5">Grupos de personas listos para actuar. "Abrir en Audiencias" para refinar con más filtros. Datos de ejemplo.</p>
      <p class="flex items-center gap-1.5 text-[10px] text-amber-600 dark:text-amber-400 font-semibold mt-1.5">
        <AlertTriangle :size="12" /> Correo, WhatsApp y Tarea aún no están conectados a un proveedor/módulo real — por ahora son solo vista previa.
      </p>
    </div>

    <!-- Filtros de la lista -->
    <div class="surface-card rounded-xl shadow-sm px-4 py-3 flex flex-wrap items-center gap-3">
      <div class="relative flex-1 min-w-[180px]">
        <Search :size="13" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input v-model="buscar" placeholder="Buscar por nombre o criterio…" class="w-full h-8 pl-8 pr-2 rounded-lg input-surface text-[11px] outline-none" />
      </div>
      <div class="flex items-center gap-1.5 text-[11px] text-muted">
        <SlidersHorizontal :size="12" /> Alcanzables:
        <button v-for="[v, l] in [['', 'Todos'], ['correo', 'Por correo'], ['celular', 'Por celular']]" :key="v"
          @click="soloAlcanzables = v as any"
          class="h-6 px-2 rounded-md border text-[10px] font-semibold transition-all"
          :class="soloAlcanzables === v ? 'bg-[#2447F9] border-[#2447F9] text-white' : 'border-default text-body hover:border-[#2447F9]'"
        >{{ l }}</button>
      </div>
      <label class="flex items-center gap-1.5 text-[11px] text-muted">
        Mín. personas
        <input v-model="minPersonas" type="number" min="0" placeholder="0" class="w-16 h-8 px-2 rounded-lg input-surface text-[11px] outline-none" />
      </label>
      <select v-model="orden" class="h-8 px-2 rounded-lg input-surface text-[11px] font-semibold outline-none cursor-pointer">
        <option value="tamano">Orden: más grandes</option>
        <option value="reciente">Orden: más recientes</option>
        <option value="nombre">Orden: nombre</option>
      </select>
    </div>

    <div v-if="aviso" class="rounded-xl bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 dark:text-white text-[12px] font-bold px-4 py-3">{{ aviso }}</div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div v-for="s in segmentos" :key="s.id" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-5">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h3 class="text-[13px] font-bold text-heading">{{ s.nombre }}</h3>
            <p class="text-[11px] text-muted mt-1 leading-relaxed">{{ s.descripcion }}</p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span class="text-[10px] text-muted whitespace-nowrap">{{ s.actualizado }}</span>
            <button
              @click="pendienteEliminar = s"
              title="Eliminar segmento"
              class="w-6 h-6 rounded-lg flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40 transition-all"
            ><Trash2 :size="12" /></button>
          </div>
        </div>

        <div class="flex flex-wrap gap-1.5 mt-3">
          <span v-for="c in s.criterios" :key="c" class="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{{ c }}</span>
        </div>

        <div class="flex items-center gap-4 mt-3 text-[11px] text-muted">
          <span class="flex items-center gap-1 font-bold text-heading"><Users :size="12" /> {{ nf.format(s.personas) }}</span>
          <span>{{ nf.format(s.conCorreo) }} con correo</span>
          <span>{{ nf.format(s.conCelular) }} con celular</span>
        </div>

        <div class="flex flex-wrap gap-2 mt-4 pt-3 border-t border-slate-100 dark:border-slate-700">
          <button @click="pedirAccion(s, 'Correo')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:border-[#2447F9] hover:text-[#2447F9] transition-all">
            <Mail :size="13" /> Correo
          </button>
          <button @click="pedirAccion(s, 'WhatsApp')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:border-[#059669] hover:text-[#059669] transition-all">
            <MessageCircle :size="13" /> WhatsApp
          </button>
          <button @click="pedirAccion(s, 'Tarea')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:border-[#C9A227] hover:text-[#C9A227] transition-all">
            <ClipboardList :size="13" /> Tarea
          </button>
          <button @click="abrirEnSegmentador(s)" class="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-[#EEF2FF] dark:bg-blue-950/40 text-[11px] font-bold text-slate-900 dark:text-white hover:bg-[#E0E7FF] dark:hover:bg-blue-950/60 transition-all ml-auto">
            Abrir en Audiencias <ArrowRight :size="13" />
          </button>
        </div>
      </div>

      <div v-if="!segmentos.length" class="lg:col-span-2 text-center text-[12px] text-muted py-12">Ningún segmento coincide con la búsqueda.</div>
    </div>

    <ConfirmDialog
      :visible="!!pendienteEliminar"
      titulo="Eliminar segmento"
      :mensaje="`¿Eliminar el segmento «${pendienteEliminar?.nombre}»? Esta acción no se puede deshacer.`"
      texto-confirmar="Eliminar"
      peligro
      @confirmar="confirmarEliminar"
      @cancelar="pendienteEliminar = null"
    />

    <ConfirmDialog
      :visible="!!pendienteAccion"
      titulo="Confirmar envío"
      :mensaje="mensajeAccion"
      texto-confirmar="Enviar"
      @confirmar="confirmarAccion"
      @cancelar="pendienteAccion = null"
    />
  </div>
</template>
