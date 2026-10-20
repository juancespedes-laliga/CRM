<script setup lang="ts">
import { computed, ref } from 'vue'
import '../../styles/graficos.css'

// Ranking de una sola serie (un color): cada fila con su etiqueta, barra y valor.
export interface BarraItem { id: string | number; label: string; valor: number; detalle?: string; sub?: string }
const props = withDefaults(defineProps<{
  items: BarraItem[]
  /** 'pct' = valor es un porcentaje 0–100 y la escala va a 100. */
  formato?: 'numero' | 'pct'
  clicable?: boolean
}>(), { formato: 'numero', clicable: false })
const emit = defineEmits<{ seleccionar: [BarraItem] }>()

const nf = new Intl.NumberFormat('es-CO')
const escala = computed(() => (props.formato === 'pct' ? 100 : Math.max(1, ...props.items.map(i => i.valor))))
const fmt = (v: number) => (props.formato === 'pct' ? `${v.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%` : nf.format(v))
const hover = ref<number | null>(null)
</script>

<template>
  <div class="mt-viz space-y-1.5">
    <component
      :is="clicable ? 'button' : 'div'"
      v-for="(it, i) in items"
      :key="it.id"
      :type="clicable ? 'button' : undefined"
      class="relative w-full grid grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_52px] items-center gap-3 text-left rounded-lg px-1.5 py-1 -mx-1.5"
      :class="clicable ? 'hover:bg-slate-50 dark:hover:bg-slate-700/40 focus-visible:outline-2 focus-visible:outline-[#2447F9]' : ''"
      @mouseenter="hover = i"
      @mouseleave="hover = null"
      @click="clicable && emit('seleccionar', it)"
    >
      <span class="min-w-0">
        <span class="block text-[11px] font-semibold text-body truncate" :title="it.label">{{ it.label }}</span>
        <span v-if="it.sub" class="block text-[10px] text-muted truncate">{{ it.sub }}</span>
      </span>
      <span class="relative h-3 rounded-full overflow-hidden" style="background: var(--mt-pista)">
        <span class="absolute inset-y-0 left-0 rounded-full transition-[width] duration-500"
          :style="{ width: `${Math.min(100, (it.valor / escala) * 100)}%`, minWidth: it.valor ? '3px' : '0', background: 'var(--mt-serie)' }" />
      </span>
      <span class="text-right text-[12px] font-bold text-heading tabular-nums">{{ fmt(it.valor) }}</span>
      <span v-if="hover === i && it.detalle" class="mt-tooltip" style="left: 60%; top: 0">{{ it.detalle }}</span>
    </component>
    <p v-if="!items.length" class="py-6 text-center text-[12px] text-muted">Sin datos.</p>
  </div>
</template>
