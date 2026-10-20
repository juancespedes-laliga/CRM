<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Layers, ChevronDown, ChevronRight, Users, FileText, Plus } from 'lucide-vue-next'
import {
  getServicios, getPlanesDeCategoria, createPlanServicio,
  type PlanServicio, type PlanDraft,
} from '../services/servicios.api'
import { PLAN_DRAFT_VACIO } from '../constants/servicios.constants'
import PlanFormDialog from '../dialogs/PlanFormDialog.vue'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'

const { gestionar: puedeGestionar } = permisosDeModulo('servicios')

const servicios = ref<string[]>([])
const cargando = ref(false)
const error = ref('')
const buscar = ref('')

const cargar = async () => {
  cargando.value = true
  error.value = ''
  try {
    servicios.value = await getServicios()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo cargar el listado de servicios.'
  } finally {
    cargando.value = false
  }
}
onMounted(cargar)

const serviciosFiltrados = computed(() => {
  const q = buscar.value.toLowerCase()
  return servicios.value.filter(s => !q || s.toLowerCase().includes(q))
})

// Detalle (planes) por categoría: se carga bajo demanda, al expandir, y se cachea para no
// repetir la petición si se vuelve a abrir la misma categoría.
const categoriaExpandida = ref<string | null>(null)
const planesPorCategoria = ref<Record<string, PlanServicio[]>>({})
const cargandoPlanes = ref<string | null>(null)
const errorPlanes = ref<Record<string, string>>({})

async function cargarPlanes(categoria: string) {
  cargandoPlanes.value = categoria
  delete errorPlanes.value[categoria]
  try {
    planesPorCategoria.value[categoria] = await getPlanesDeCategoria(categoria)
  } catch (e) {
    errorPlanes.value[categoria] = e instanceof Error ? e.message : 'No se pudieron cargar los planes.'
  } finally {
    cargandoPlanes.value = null
  }
}

async function alternarCategoria(categoria: string) {
  if (categoriaExpandida.value === categoria) {
    categoriaExpandida.value = null
    return
  }
  categoriaExpandida.value = categoria
  if (!planesPorCategoria.value[categoria]) await cargarPlanes(categoria)
}

// ── Nuevo servicio / nuevo plan ────────────────────────────────────
const modalVisible = ref(false)
const categoriaFija = ref<string | undefined>(undefined)
const draft = ref<PlanDraft>({ ...PLAN_DRAFT_VACIO })
const errorGuardar = ref<string | null>(null)

const abrirNuevoServicio = () => {
  categoriaFija.value = undefined
  draft.value = { ...PLAN_DRAFT_VACIO }
  errorGuardar.value = null
  modalVisible.value = true
}
const abrirNuevoPlan = (categoria: string) => {
  categoriaFija.value = categoria
  draft.value = { ...PLAN_DRAFT_VACIO, categoria }
  errorGuardar.value = null
  modalVisible.value = true
}

const guardar = async () => {
  errorGuardar.value = null
  try {
    await createPlanServicio(draft.value)
    const categoria = draft.value.categoria
    const esServicioNuevo = !servicios.value.includes(categoria)
    if (esServicioNuevo) servicios.value = [...servicios.value, categoria].sort()
    if (planesPorCategoria.value[categoria]) await cargarPlanes(categoria)
    categoriaExpandida.value = categoria
    modalVisible.value = false
  } catch (e) {
    errorGuardar.value = e instanceof Error ? e.message : 'No se pudo guardar.'
  }
}
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
          Servicios Plan Liga
          <span class="bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 dark:text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full">{{ servicios.length }}</span>
        </h2>
        <p class="text-[12px] text-muted mt-0.5">Categorías de servicio registradas en el portal</p>
      </div>
      <button v-if="puedeGestionar" @click="abrirNuevoServicio" class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all shrink-0">
        <Plus :size="14" /> Agregar servicio
      </button>
    </div>

    <div v-if="error" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 text-[12px] px-4 py-3">
      {{ error }}
    </div>

    <div class="surface-card rounded-2xl shadow-sm px-4 py-3">
      <div class="relative">
        <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
        <input v-model="buscar" placeholder="Buscar servicio..." class="w-full h-9 pl-9 pr-4 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all" />
      </div>
    </div>

    <div v-if="cargando" class="surface-card rounded-2xl shadow-sm px-4 py-16 text-center text-muted text-[12px]">
      Cargando servicios...
    </div>
    <div v-else class="surface-card rounded-2xl shadow-sm overflow-hidden divide-y divide-slate-100 dark:divide-slate-700">
      <div v-for="s in serviciosFiltrados" :key="s">
        <button
          type="button"
          @click="alternarCategoria(s)"
          class="w-full flex items-center gap-3 px-5 py-3.5 text-left surface-hover transition-colors cursor-pointer"
        >
          <div class="w-9 h-9 rounded-xl bg-[#FEF9C3] dark:bg-amber-950/50 text-[#C9A227] dark:text-amber-400 font-bold text-[11px] flex items-center justify-center flex-shrink-0">
            <Layers :size="16" />
          </div>
          <span class="text-[12px] font-semibold text-heading flex-1">{{ s }}</span>
          <span class="flex items-center gap-1 text-[11px] font-bold text-slate-900 dark:text-white shrink-0">
            {{ categoriaExpandida === s ? 'Ver menos' : 'Ver más' }}
            <component :is="categoriaExpandida === s ? ChevronDown : ChevronRight" :size="14" />
          </span>
        </button>

        <div v-if="categoriaExpandida === s" class="bg-slate-50 dark:bg-slate-900/40 px-5 py-3 space-y-2">
          <div v-if="cargandoPlanes === s" class="text-center py-6 text-muted text-[12px]">Cargando planes...</div>
          <div v-else-if="errorPlanes[s]" class="text-[12px] text-red-600 dark:text-red-400 py-2">{{ errorPlanes[s] }}</div>
          <template v-else>
            <div
              v-for="plan in planesPorCategoria[s]"
              :key="plan.id"
              class="surface-card rounded-xl px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4"
            >
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-[12px] font-semibold text-heading">{{ plan.nombre }}</span>
                  <span
                    class="text-[10px] font-bold px-1.5 py-0.5 rounded"
                    :class="plan.estado === 'Activo' ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40' : 'text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800'"
                  >{{ plan.estado }}</span>
                  <span class="text-[10px] font-semibold text-muted">{{ plan.tipoCliente }}</span>
                </div>
                <p v-if="plan.descripcion" class="text-[11px] text-muted mt-0.5">{{ plan.descripcion }}</p>
              </div>
              <div class="flex items-center gap-1.5 text-[11px] text-body shrink-0">
                <Users :size="12" class="text-slate-400 dark:text-slate-500" />
                {{ plan.beneficiarios }} benef.<span v-if="plan.beneficiariosAdicionales"> (+{{ plan.beneficiariosAdicionales }} adic.)</span>
              </div>
            </div>
            <div v-if="planesPorCategoria[s]?.length === 0" class="text-center py-6 text-muted text-[12px] flex items-center justify-center gap-1.5">
              <FileText :size="13" /> Sin planes registrados en esta categoría.
            </div>
            <button
              v-if="puedeGestionar"
              type="button"
              @click="abrirNuevoPlan(s)"
              class="w-full flex items-center justify-center gap-1.5 h-9 rounded-xl border border-dashed border-[#2447F9]/40 dark:border-blue-400/30 text-[11px] font-bold text-slate-900 dark:text-white hover:bg-[#EEF2FF] dark:hover:bg-blue-950/30 transition-all cursor-pointer"
            >
              <Plus :size="13" /> Agregar plan a "{{ s }}"
            </button>
          </template>
        </div>
      </div>
      <div v-if="serviciosFiltrados.length === 0" class="text-center py-16 text-muted text-[12px]">
        No se encontraron servicios.
      </div>
    </div>

    <PlanFormDialog
      v-model:visible="modalVisible"
      v-model:draft="draft"
      :categoria-fija="categoriaFija"
      :error="errorGuardar"
      @submit="guardar"
    />
  </div>
</template>
