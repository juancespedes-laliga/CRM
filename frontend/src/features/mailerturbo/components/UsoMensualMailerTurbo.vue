<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Gauge, Loader2 } from 'lucide-vue-next'
import type { UsoMensualMT } from '../types/mailerturbo'
import { getUsoMensual } from '../services/mailerturbo.api'

// Contador del cupo de MailerTurbo: correos enviados este mes, disponibles y
// total mensual del plan (MAILERTURBO_LIMITE_MENSUAL en el backend).
const nf = new Intl.NumberFormat('es-CO')
const uso = ref<UsoMensualMT | null>(null)
const cargando = ref(false)
const error = ref<string | null>(null)

async function cargar() {
  cargando.value = true
  error.value = null
  try {
    uso.value = await getUsoMensual()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo consultar el uso del mes.'
  } finally {
    cargando.value = false
  }
}
onMounted(() => void cargar())
defineExpose({ cargar })

const nombreMes = computed(() => {
  if (!uso.value) return ''
  const [a, m] = uso.value.mes.split('-').map(Number)
  return new Date(a, m - 1, 1).toLocaleDateString('es-CO', { month: 'long', year: 'numeric' })
})
const porcentaje = computed(() => {
  const u = uso.value
  return u?.limiteMensual ? Math.min(100, (u.enviados / u.limiteMensual) * 100) : 0
})
const colorBarra = computed(() =>
  porcentaje.value >= 90 ? 'bg-red-500' : porcentaje.value >= 70 ? 'bg-amber-500' : 'bg-[#2447F9]',
)
// Sin MAILERTURBO_LIMITE_MENSUAL solo se muestran los enviados.
const indicadores = computed(() => [
  { label: 'Enviados', valor: uso.value?.enviados, color: 'text-heading' },
  ...(uso.value?.limiteMensual ? [
    { label: 'Disponibles', valor: uso.value.disponibles, color: 'text-emerald-600 dark:text-emerald-400' },
    { label: 'Total mensual', valor: uso.value.limiteMensual, color: 'text-heading' },
  ] : []),
])
const fmt = (n: number | null | undefined) => (n == null ? '—' : nf.format(n))
</script>

<template>
  <div class="surface-card rounded-2xl shadow-sm px-4 py-3">
    <div class="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
      <div class="flex items-center gap-2 min-w-0">
        <div class="w-8 h-8 rounded-lg bg-[#EEF2FF] dark:bg-blue-950/50 grid place-items-center shrink-0">
          <Gauge :size="16" class="text-[#2447F9]" />
        </div>
        <div class="min-w-0">
          <h3 class="text-[13px] font-bold text-heading">Cupo de envíos del mes</h3>
          <p class="text-[11px] text-muted first-letter:uppercase">{{ nombreMes || 'Mes actual' }}</p>
        </div>
      </div>

      <div class="flex items-center gap-6">
        <div v-for="k in indicadores" :key="k.label" class="text-right">
          <div class="text-[10px] font-bold text-subtle uppercase tracking-wide">{{ k.label }}</div>
          <div class="text-[18px] font-bold tabular-nums leading-tight" :class="k.color">
            <Loader2 v-if="cargando && !uso" :size="15" class="animate-spin text-muted inline" />
            <template v-else>{{ fmt(k.valor) }}</template>
          </div>
        </div>
      </div>
    </div>

    <div v-if="uso?.limiteMensual" class="mt-3">
      <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
        <div class="h-full rounded-full transition-all" :class="colorBarra" :style="{ width: `${porcentaje}%` }" />
      </div>
      <p class="text-[10px] text-muted mt-1 tabular-nums">{{ porcentaje.toFixed(1) }}% del cupo usado</p>
    </div>
    <p v-if="error" class="text-[11px] text-red-500 mt-2">{{ error }}</p>
  </div>
</template>
