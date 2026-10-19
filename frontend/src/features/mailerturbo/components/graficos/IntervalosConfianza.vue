<script setup lang="ts">
import { computed } from 'vue'
import '../../styles/graficos.css'

// Tasa de cada elemento con su intervalo de confianza del 95% (Wilson).
// Un intervalo angosto = la tasa es precisa (muchos envíos); uno ancho = pocos datos.
export interface ItemIntervalo { id: string | number; label: string; sub?: string; valor: number | null; inf: number | null; sup: number | null }
const props = defineProps<{ items: ItemIntervalo[] }>()

const COLORES = ['var(--mt-s1)', 'var(--mt-s2)', 'var(--mt-s3)']
const fmt = (v: number | null) => (v == null ? '—' : `${v.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`)
const maximo = computed(() => {
  const m = Math.max(1, ...props.items.map(i => i.sup ?? i.valor ?? 0))
  const paso = m > 50 ? 20 : m > 20 ? 10 : m > 5 ? 5 : 1
  return Math.min(100, Math.ceil((m * 1.08) / paso) * paso)
})
const pos = (v: number) => `${(v / maximo.value) * 100}%`
const ticks = computed(() => [0, 0.25, 0.5, 0.75, 1].map(f => +(maximo.value * f).toFixed(1)))
</script>

<template>
  <div class="mt-viz">
    <div class="grid grid-cols-[minmax(0,180px)_1fr_120px] gap-x-3 items-center">
      <template v-for="(it, i) in items" :key="it.id">
        <div class="min-w-0 py-2">
          <div class="flex items-center gap-1.5 text-[11px] font-semibold text-body truncate" :title="it.label">
            <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ background: COLORES[i % 3] }" />{{ it.label }}
          </div>
          <div v-if="it.sub" class="text-[10px] text-muted truncate pl-4">{{ it.sub }}</div>
        </div>
        <div class="relative h-8">
          <div v-for="t in ticks" :key="t" class="absolute inset-y-0 border-l" :style="{ left: pos(t), borderColor: 'var(--mt-grid)' }" />
          <template v-if="it.valor != null && it.inf != null && it.sup != null">
            <div class="absolute top-1/2 h-[3px] -translate-y-1/2 rounded-full" :style="{ left: pos(it.inf), width: `calc(${pos(it.sup)} - ${pos(it.inf)})`, background: COLORES[i % 3], opacity: 0.45 }" />
            <div class="absolute top-1/2 h-3 w-[2px] -translate-y-1/2" :style="{ left: pos(it.inf), background: COLORES[i % 3] }" />
            <div class="absolute top-1/2 h-3 w-[2px] -translate-y-1/2" :style="{ left: pos(it.sup), background: COLORES[i % 3] }" />
            <div class="absolute top-1/2 w-3 h-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-white dark:ring-slate-800" :style="{ left: pos(it.valor), background: COLORES[i % 3] }" />
          </template>
          <span v-else class="absolute inset-0 flex items-center text-[10px] text-muted">Sin envíos</span>
        </div>
        <div class="text-right leading-tight">
          <div class="text-[12px] font-bold text-heading tabular-nums">{{ fmt(it.valor) }}</div>
          <div class="text-[10px] text-muted tabular-nums">IC 95%: {{ fmt(it.inf) }} – {{ fmt(it.sup) }}</div>
        </div>
      </template>
      <div />
      <div class="relative h-4">
        <span v-for="t in ticks" :key="t" class="absolute -translate-x-1/2 text-[10px] text-muted tabular-nums" :style="{ left: pos(t) }">{{ fmt(t) }}</span>
      </div>
      <div />
    </div>
  </div>
</template>
