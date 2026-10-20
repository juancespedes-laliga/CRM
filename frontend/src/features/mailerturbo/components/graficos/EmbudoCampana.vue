<script setup lang="ts">
import { computed, ref } from 'vue'
import '../../styles/graficos.css'

// Embudo de la campaña: cada etapa como barra horizontal sobre la misma escala
// (el total de destinatarios). Clic en una etapa = filtrar la tabla por ella.
export interface EtapaEmbudo { id: string; label: string; valor: number }
const props = defineProps<{ etapas: EtapaEmbudo[] }>()
const emit = defineEmits<{ seleccionar: [string] }>()

const nf = new Intl.NumberFormat('es-CO')
const COLORES = ['var(--mt-embudo-1)', 'var(--mt-embudo-2)', 'var(--mt-embudo-3)', 'var(--mt-embudo-4)']

const base = computed(() => props.etapas[0]?.valor || 0)
const pct = (n: number, de: number) => (de ? (n / de) * 100 : 0)
const fmtPct = (n: number) => `${n.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`

const hover = ref<number | null>(null)
</script>

<template>
  <div class="mt-viz space-y-2.5">
    <button
      v-for="(e, i) in etapas"
      :key="e.id"
      type="button"
      class="relative w-full grid grid-cols-[96px_1fr_92px] items-center gap-3 text-left rounded-lg px-1.5 py-1 -mx-1.5 hover:bg-slate-50 dark:hover:bg-slate-700/40 focus-visible:outline-2 focus-visible:outline-[#2447F9]"
      :aria-label="`${e.label}: ${nf.format(e.valor)} (${fmtPct(pct(e.valor, base))}). Ver en la tabla`"
      @mouseenter="hover = i"
      @mouseleave="hover = null"
      @focus="hover = i"
      @blur="hover = null"
      @click="emit('seleccionar', e.id)"
    >
      <span class="text-[11px] font-semibold text-body truncate">{{ e.label }}</span>
      <span class="relative h-6 rounded-md overflow-hidden" style="background: var(--mt-pista)">
        <span
          class="absolute inset-y-0 left-0 rounded-r-[4px] transition-[width] duration-500"
          :style="{ width: `${Math.max(pct(e.valor, base), e.valor ? 0.8 : 0)}%`, background: COLORES[i] ?? COLORES[3] }"
        />
      </span>
      <span class="text-right leading-tight">
        <span class="block text-[12px] font-bold text-heading tabular-nums">{{ nf.format(e.valor) }}</span>
        <span class="block text-[10px] text-muted tabular-nums">{{ fmtPct(pct(e.valor, base)) }}</span>
      </span>
      <span v-if="hover === i" class="mt-tooltip" style="left: 50%; top: 0">
        <strong>{{ e.label }}</strong> · {{ nf.format(e.valor) }}<br />
        {{ fmtPct(pct(e.valor, base)) }} de {{ etapas[0].label.toLowerCase() }}
        <template v-if="i > 0"> · {{ fmtPct(pct(e.valor, etapas[i - 1].valor)) }} de {{ etapas[i - 1].label.toLowerCase() }}</template>
        <br /><span class="opacity-70">Clic para ver la lista</span>
      </span>
    </button>
  </div>
</template>
