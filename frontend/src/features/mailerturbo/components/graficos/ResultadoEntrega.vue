<script setup lang="ts">
import { computed, ref } from 'vue'
import { CircleCheck, TriangleAlert, CircleX } from 'lucide-vue-next'
import '../../styles/graficos.css'

// Parte-del-todo de la entrega: barra 100% con segmentos de estado
// (cada estado lleva ícono + texto, nunca solo color).
const props = defineProps<{ entregados: number; rebotes: number; otrosNoEnviados: number }>()
const emit = defineEmits<{ seleccionar: [string] }>()
const nf = new Intl.NumberFormat('es-CO')

const segmentos = computed(() => {
  const total = props.entregados + props.rebotes + props.otrosNoEnviados
  return [
    { id: 'enviados', label: 'Entregados', valor: props.entregados, color: 'var(--mt-bien)', icono: CircleCheck },
    { id: 'no_enviados', label: 'Rebotados', valor: props.rebotes, color: 'var(--mt-serio)', icono: TriangleAlert },
    { id: 'no_enviados', label: 'Sin enviar / rechazados', valor: props.otrosNoEnviados, color: 'var(--mt-critico)', icono: CircleX },
  ].map(s => ({ ...s, pct: total ? (s.valor / total) * 100 : 0 }))
})
const visibles = computed(() => segmentos.value.filter(s => s.valor > 0))
const fmtPct = (n: number) => `${n.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`
const hover = ref<string | null>(null)
</script>

<template>
  <div class="mt-viz">
    <div class="relative flex h-7 w-full gap-[2px] rounded-md overflow-visible" role="img"
      :aria-label="segmentos.map(s => `${s.label} ${nf.format(s.valor)}`).join(', ')">
      <div v-if="!visibles.length" class="flex-1 rounded-md" style="background: var(--mt-pista)" />
      <button
        v-for="(s, i) in visibles"
        :key="s.label"
        type="button"
        class="relative h-full transition-[flex-grow] duration-500 focus-visible:outline-2 focus-visible:outline-[#2447F9]"
        :class="[i === 0 ? 'rounded-l-[4px]' : '', i === visibles.length - 1 ? 'rounded-r-[4px]' : '']"
        :style="{ flexGrow: Math.max(s.pct, 0.6), flexBasis: 0, background: s.color }"
        @mouseenter="hover = s.label"
        @mouseleave="hover = null"
        @click="emit('seleccionar', s.id)"
      >
        <span v-if="hover === s.label" class="mt-tooltip" style="left: 50%; top: 0">
          <strong>{{ s.label }}</strong> · {{ nf.format(s.valor) }} ({{ fmtPct(s.pct) }})
        </span>
      </button>
    </div>
    <ul class="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2">
      <li v-for="s in segmentos" :key="s.label">
        <button type="button" class="w-full flex items-center gap-2 text-left rounded-lg px-1.5 py-1 hover:bg-slate-50 dark:hover:bg-slate-700/40" @click="emit('seleccionar', s.id)">
          <component :is="s.icono" :size="14" :style="{ color: s.color }" class="shrink-0" />
          <span class="min-w-0">
            <span class="block text-[11px] text-muted truncate">{{ s.label }}</span>
            <span class="block text-[13px] font-bold text-heading tabular-nums">
              {{ nf.format(s.valor) }} <span class="text-[10px] font-semibold text-muted">{{ fmtPct(s.pct) }}</span>
            </span>
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>
