<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Search, Loader2, CheckCircle2, XCircle, Activity } from 'lucide-vue-next'
import {
  getResumenUsoPlan, buscarUsoPlan,
  type ResumenUsoPlan, type UsoPlanPersona,
} from '../services/segmentos.api'

const nf = new Intl.NumberFormat('es-CO')

const resumen = ref<ResumenUsoPlan | null>(null)
const cargandoResumen = ref(true)
const errorResumen = ref<string | null>(null)

const cargarResumen = async () => {
  cargandoResumen.value = true
  errorResumen.value = null
  try {
    resumen.value = await getResumenUsoPlan()
  } catch (e) {
    errorResumen.value = e instanceof Error ? e.message : 'No se pudo cargar el resumen de uso del plan.'
  } finally {
    cargandoResumen.value = false
  }
}
onMounted(cargarResumen)

const categorias = computed(() => resumen.value ? [
  { label: 'Total', cat: resumen.value.total },
  { label: 'Titulares', cat: resumen.value.titulares },
  { label: 'Beneficiarios', cat: resumen.value.beneficiarios },
] : [])

// Una sola escala para las 6 barras (2 por categoria: activos y con uso), en
// vez de escalar cada categoria contra si misma -- si no, Titulares (1.983
// activos) y Beneficiarios (5.079) se verian del mismo tamaño en vez de
// reflejar la diferencia real. El techo es Total.activos: es el numero mas
// grande del grupo (Total = Titulares + Beneficiarios), asi que todo lo
// demas siempre cabe por debajo del 100%.
const maxActivos = computed(() => resumen.value?.total.activos || 1)
const alturaPct = (valor: number) => {
  if (!maxActivos.value) return 0
  const pct = (valor / maxActivos.value) * 100
  return valor > 0 ? Math.max(pct, 2) : 0
}

const documentoBuscar = ref('')
const buscando = ref(false)
const errorBusqueda = ref<string | null>(null)
const resultado = ref<UsoPlanPersona | null>(null)

const buscar = async () => {
  const documento = documentoBuscar.value.trim()
  if (!documento) return
  buscando.value = true
  errorBusqueda.value = null
  resultado.value = null
  try {
    resultado.value = await buscarUsoPlan(documento)
  } catch (e) {
    errorBusqueda.value = e instanceof Error ? e.message : 'No se pudo buscar el documento.'
  } finally {
    buscando.value = false
  }
}
</script>

<template>
  <div class="surface-card rounded-xl shadow-sm p-4 space-y-4 shrink-0">
    <div class="flex items-center justify-between">
      <h3 class="text-[12px] font-bold text-heading flex items-center gap-1.5">
        <Activity :size="14" class="text-[#EC4899]" /> Uso de Plan Liga
      </h3>
      <Loader2 v-if="cargandoResumen" :size="14" class="animate-spin text-[#2447F9]" />
    </div>

    <p v-if="errorResumen" class="text-[11px] font-semibold text-red-600 dark:text-red-400">{{ errorResumen }}</p>

    <div v-else-if="resumen">
      <!-- 2 series (Activos, Con uso) x 3 categorias = 6 barras, todas en la
      misma escala (ver maxActivos) para que se puedan comparar magnitudes
      reales entre categorias, no solo el % de cada una por separado. -->
      <div class="flex items-center gap-3 mb-2 text-[10px] font-semibold text-subtle">
        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-sm bg-slate-300 dark:bg-slate-600 shrink-0" /> Activos</span>
        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-sm bg-emerald-600 dark:bg-emerald-400 shrink-0" /> Con uso</span>
      </div>

      <div class="flex items-end justify-around gap-5 h-28 border-b border-default">
        <div v-for="c in categorias" :key="c.label" class="flex items-end justify-center gap-1.5 h-full flex-1 max-w-[130px]">
          <div class="flex flex-col items-center justify-end h-full">
            <span class="text-[9px] font-bold text-heading tabular-nums mb-1">{{ nf.format(c.cat.activos) }}</span>
            <div class="w-7 sm:w-8 rounded-t-md bg-slate-300 dark:bg-slate-600 transition-all" :style="{ height: alturaPct(c.cat.activos) + '%' }" />
          </div>
          <div class="flex flex-col items-center justify-end h-full">
            <span class="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 tabular-nums mb-1">{{ nf.format(c.cat.conUso) }}</span>
            <div class="w-7 sm:w-8 rounded-t-md bg-emerald-600 dark:bg-emerald-400 transition-all" :style="{ height: alturaPct(c.cat.conUso) + '%' }" />
          </div>
        </div>
      </div>
      <div class="flex items-start justify-around gap-5 mt-1.5">
        <div v-for="c in categorias" :key="c.label" class="flex-1 max-w-[130px] text-center">
          <div class="text-[10px] font-bold text-subtle uppercase tracking-wide">{{ c.label }}</div>
          <div class="text-[9px] text-muted mt-0.5">{{ c.cat.porcentajeUso }}% usó</div>
        </div>
      </div>
    </div>

    <div class="pt-3 border-t border-default">
      <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-1.5">Buscar por documento</label>
      <div class="flex gap-2">
        <div class="relative flex-1">
          <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            v-model="documentoBuscar"
            @keydown.enter="buscar"
            placeholder="Cédula del titular o beneficiario"
            class="w-full h-8 pl-8 pr-2 rounded-lg input-surface text-[11px] outline-none"
          />
        </div>
        <button
          @click="buscar"
          :disabled="buscando || !documentoBuscar.trim()"
          class="h-8 px-3 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50 flex items-center gap-1.5 shrink-0"
        >
          <Loader2 v-if="buscando" :size="12" class="animate-spin" />
          Buscar
        </button>
      </div>

      <p v-if="errorBusqueda" class="text-[11px] font-semibold text-red-600 dark:text-red-400 mt-2">{{ errorBusqueda }}</p>

      <div v-if="resultado" class="mt-2.5 rounded-lg border border-default p-3 flex items-start justify-between gap-3">
        <div class="min-w-0">
          <div class="text-[12px] font-bold text-heading truncate">{{ resultado.nombre }}</div>
          <div class="text-[10px] text-muted mt-0.5">
            CC {{ resultado.documento }} · {{ resultado.tipo === 'titular' ? 'Titular' : 'Beneficiario' }} · {{ resultado.estado }}
          </div>
          <div v-if="resultado.haUsado" class="text-[10px] text-muted mt-0.5">
            {{ resultado.serviciosUsados }} servicio(s) · último uso {{ resultado.ultimoUso ?? '—' }}
          </div>
        </div>
        <span
          class="shrink-0 inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full"
          :class="resultado.haUsado
            ? 'bg-[#D1FAE5] text-[#059669] dark:bg-emerald-950/50 dark:text-emerald-400'
            : 'bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400'"
        >
          <CheckCircle2 v-if="resultado.haUsado" :size="12" />
          <XCircle v-else :size="12" />
          {{ resultado.haUsado ? 'Ha usado el plan' : 'No lo ha usado' }}
        </span>
      </div>
    </div>
  </div>
</template>
