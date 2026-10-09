<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Plus, Filter, Loader2, AlertCircle, CheckCircle2, X, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { Actividad, ActividadDraft } from '../types/actividad'
import { ACTIVIDAD_DRAFT_VACIO } from '../constants/relacionamiento.constants'
import { useRelacionamiento } from '../composables/useRelacionamiento'
import type { Oportunidad } from '@/features/oportunidades/types/oportunidad'
import { getOportunidades } from '@/features/oportunidades/services/oportunidades.api'
import FiltrosTipo from '../components/FiltrosTipo.vue'
import TimelineItem from '../components/TimelineItem.vue'
import PendientesAlerta from '../components/PendientesAlerta.vue'
import ActividadFormDialog from '../dialogs/ActividadFormDialog.vue'
import ConfirmarEliminarActividadDialog from '../dialogs/ConfirmarEliminarActividadDialog.vue'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'

const { gestionar: puedeGestionar } = permisosDeModulo('bitacora')

const {
  actividades, cargando, filtroTipo, filtroUsuario, buscar,
  actividadesFiltradas, usuarios, pendientes,
  paginaActual, actividadesPaginadas, totalPaginas,
  crearActividad, actualizarActividad, guardandoActividad, errorGuardarActividad,
  eliminarActividad, eliminandoActividad, errorEliminarActividad,
  marcarRealizada, completandoId, errorCompletarActividad,
} = useRelacionamiento()

// Se carga una sola vez acá (no en cada TimelineItem) para que "oportunidad relacionada"
// se pueda mostrar por fila sin un fetch por actividad.
const oportunidades = ref<Oportunidad[]>([])
onMounted(async () => { oportunidades.value = await getOportunidades().catch(() => []) })

const avisoRealizado = ref<string | null>(null)
const marcarRealizado = async (a: Actividad) => {
  const ok = await marcarRealizada(a.id)
  if (ok) avisoRealizado.value = `"${a.proximoPaso}" quedó marcado como realizado y salió de pendientes.`
}

const modalVisible = ref(false)
const modalModo = ref<'nuevo' | 'editar'>('nuevo')
const draft = ref<ActividadDraft>({ ...ACTIVIDAD_DRAFT_VACIO })
const actividadEditandoId = ref<number | null>(null)

const abrirNuevo = () => {
  modalModo.value = 'nuevo'
  actividadEditandoId.value = null
  draft.value = { ...ACTIVIDAD_DRAFT_VACIO, fecha: new Date().toISOString().split('T')[0] }
  errorGuardarActividad.value = null
  modalVisible.value = true
}

const abrirEditar = (a: Actividad) => {
  modalModo.value = 'editar'
  actividadEditandoId.value = a.id
  draft.value = { ...a }
  errorGuardarActividad.value = null
  modalVisible.value = true
}

const guardar = async () => {
  const ok = modalModo.value === 'editar' && actividadEditandoId.value !== null
    ? await actualizarActividad(actividadEditandoId.value, draft.value)
    : await crearActividad(draft.value)
  if (ok) modalVisible.value = false
}

const actividadEliminando = ref<Actividad | null>(null)
const abrirEliminar = (a: Actividad) => {
  errorEliminarActividad.value = null
  actividadEliminando.value = a
}
const confirmarEliminar = async () => {
  if (!actividadEliminando.value) return
  const ok = await eliminarActividad(actividadEliminando.value.id)
  if (ok) actividadEliminando.value = null
}
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
          Bitácora de Relacionamiento
          <span class="bg-[#EEF2FF] dark:bg-blue-950/50 text-slate-900 dark:text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full">{{ actividades.length }}</span>
        </h2>
        <p class="text-[12px] text-body mt-0.5">Historial completo de interacciones · llamadas, correos, reuniones</p>
      </div>
      <button v-if="puedeGestionar" @click="abrirNuevo" class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all">
        <Plus :size="14" /> Registrar actividad
      </button>
    </div>

    <div v-if="avisoRealizado" class="flex items-center gap-2.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl px-4 py-3">
      <CheckCircle2 :size="16" class="text-emerald-600 dark:text-emerald-400 shrink-0" />
      <p class="text-[12px] font-semibold text-emerald-700 dark:text-emerald-300">{{ avisoRealizado }}</p>
      <button @click="avisoRealizado = null" class="ml-auto text-emerald-400 hover:text-emerald-600 dark:hover:text-emerald-300 shrink-0"><X :size="13" /></button>
    </div>

    <PendientesAlerta :pendientes="pendientes" :completando="completandoId" @abrir="abrirEditar" @completar="marcarRealizado" />

    <div v-if="errorCompletarActividad" class="flex items-center gap-2.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-4 py-3">
      <AlertCircle :size="16" class="text-red-500 dark:text-red-400 shrink-0" />
      <p class="text-[12px] font-semibold text-red-600 dark:text-red-400">{{ errorCompletarActividad }}</p>
    </div>

    <FiltrosTipo :actividades="actividades" :filtro-tipo="filtroTipo" @update:filtro-tipo="filtroTipo = $event" />

    <div class="surface-card rounded-2xl shadow-sm px-4 py-3">
      <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
        <div class="relative flex-1 min-w-0">
          <Filter :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
          <input v-model="buscar" placeholder="Buscar por contacto, cédula, empresa o acción..." class="w-full h-9 pl-9 pr-4 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] dark:focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
        <select v-model="filtroUsuario" class="h-9 px-3 rounded-lg input-surface text-[11px] font-medium outline-none cursor-pointer">
          <option value="todos">Todos los usuarios</option>
          <option v-for="u in usuarios" :key="u" :value="u">{{ u }}</option>
        </select>
      </div>
      <div class="mt-2 text-[11px] text-muted">
        Mostrando <strong class="text-body">{{ actividadesFiltradas.length }}</strong> actividades
      </div>
    </div>

    <div v-if="cargando" class="flex items-center justify-center gap-2 surface-card rounded-2xl p-16 text-muted text-[12px]">
      <Loader2 :size="16" class="animate-spin" />Cargando bitácora...
    </div>
    <div v-else class="space-y-3">
      <TimelineItem v-for="a in actividadesPaginadas" :key="a.id" :actividad="a" :oportunidades="oportunidades" @eliminar="abrirEliminar(a)" @editar="abrirEditar(a)" />

      <div v-if="actividadesFiltradas.length === 0" class="surface-card rounded-2xl p-16 text-center text-muted text-[12px]">
        No se encontraron actividades con los filtros aplicados.
      </div>

      <div v-if="totalPaginas > 1" class="flex items-center justify-center gap-3 surface-card rounded-2xl px-1 py-3">
        <button @click="paginaActual -= 1" :disabled="paginaActual <= 1"
          class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          title="Página anterior">
          <ChevronLeft :size="15" />
        </button>
        <span class="text-[11px] text-muted">Página <strong class="text-body">{{ paginaActual }}</strong> de <strong class="text-body">{{ totalPaginas }}</strong></span>
        <button @click="paginaActual += 1" :disabled="paginaActual >= totalPaginas"
          class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          title="Página siguiente">
          <ChevronRight :size="15" />
        </button>
      </div>
    </div>

    <ActividadFormDialog v-model:visible="modalVisible" v-model:draft="draft" :modo="modalModo" :guardando="guardandoActividad" :error="errorGuardarActividad" @submit="guardar" />

    <ConfirmarEliminarActividadDialog
      :actividad="actividadEliminando"
      :eliminando="eliminandoActividad"
      :error="errorEliminarActividad"
      @confirmar="confirmarEliminar"
      @cancelar="actividadEliminando = null"
    />
  </div>
</template>
