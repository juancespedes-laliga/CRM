<script setup lang="ts">
import { computed, ref } from 'vue'
import '../../styles/graficos.css'

// Torta (parte de un todo, máximo 6 porciones). Color fijo por posición; la porción
// con id 'otros' va en gris. La leyenda siempre muestra valor y %, así la
// identidad nunca depende solo del color.
export interface PorcionTorta { id: string | number; label: string; valor: number; detalle?: string }
const props = withDefaults(defineProps<{ porciones: PorcionTorta[]; tamano?: number; unidad?: string }>(), { tamano: 180, unidad: '' })

const COLORES = ['var(--mt-s1)', 'var(--mt-s2)', 'var(--mt-s3)', 'var(--mt-s4)', 'var(--mt-s5)']
const nf = new Intl.NumberFormat('es-CO')
const total = computed(() => props.porciones.reduce((s, p) => s + Math.max(0, p.valor), 0))
const pct = (v: number) => (total.value ? (v / total.value) * 100 : 0)
const fmtPct = (v: number) => `${v.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`

const r = computed(() => props.tamano / 2 - 4)
const c = computed(() => props.tamano / 2)
const punto = (ang: number, radio = r.value) => [c.value + radio * Math.sin(ang), c.value - radio * Math.cos(ang)]

const arcos = computed(() => {
  let ang = 0
  let ci = 0
  return props.porciones.map(p => {
    const color = p.id === 'otros' ? 'var(--mt-otros)' : COLORES[ci++ % COLORES.length]
    const frac = total.value ? Math.max(0, p.valor) / total.value : 0
    const a0 = ang, a1 = ang + frac * 2 * Math.PI
    ang = a1
    const [x0, y0] = punto(a0), [x1, y1] = punto(a1)
    const d = frac >= 0.9999
      ? null
      : `M${c.value},${c.value} L${x0},${y0} A${r.value},${r.value} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${x1},${y1} Z`
    const medio = (a0 + a1) / 2
    return { ...p, color, frac, d, medio }
  })
})
const hover = ref<number | null>(null)
const desplazar = (i: number) => {
  if (hover.value !== i) return ''
  const [dx, dy] = [Math.sin(arcos.value[i].medio) * 5, -Math.cos(arcos.value[i].medio) * 5]
  return `translate(${dx} ${dy})`
}
</script>

<template>
  <div class="mt-viz flex flex-col sm:flex-row items-center gap-5">
    <div class="relative shrink-0">
      <svg :width="tamano" :height="tamano" role="img" :aria-label="porciones.map(p => `${p.label} ${fmtPct(pct(p.valor))}`).join(', ')">
        <circle v-if="!total" :cx="c" :cy="c" :r="r" fill="var(--mt-pista)" />
        <template v-for="(a, i) in arcos" :key="a.id">
          <circle v-if="a.frac && !a.d" :cx="c" :cy="c" :r="r" :fill="a.color" />
          <path
            v-else-if="a.frac"
            :d="a.d!"
            :fill="a.color"
            stroke="var(--mt-superficie)"
            stroke-width="2"
            stroke-linejoin="round"
            :transform="desplazar(i)"
            class="transition-transform duration-150 cursor-default"
            :opacity="hover === null || hover === i ? 1 : 0.55"
            @mouseenter="hover = i"
            @mouseleave="hover = null"
          />
        </template>
      </svg>
      <div v-if="hover !== null" class="mt-tooltip" :style="{ left: '50%', top: '0' }">
        <strong>{{ arcos[hover].label }}</strong> · {{ nf.format(arcos[hover].valor) }}{{ unidad ? ` ${unidad}` : '' }} ({{ fmtPct(pct(arcos[hover].valor)) }})
        <div v-if="arcos[hover].detalle" class="opacity-70">{{ arcos[hover].detalle }}</div>
      </div>
    </div>
    <ul class="w-full min-w-0 space-y-1">
      <li
        v-for="(a, i) in arcos"
        :key="a.id"
        class="flex items-center gap-2 rounded-md px-1.5 py-1 text-[11px]"
        :class="hover === i ? 'bg-slate-50 dark:bg-slate-700/50' : ''"
        @mouseenter="hover = i"
        @mouseleave="hover = null"
      >
        <span class="w-2.5 h-2.5 rounded-sm shrink-0" :style="{ background: a.color }" />
        <span class="flex-1 min-w-0 truncate text-body" :title="a.label">{{ a.label }}</span>
        <span class="tabular-nums text-muted">{{ nf.format(a.valor) }}</span>
        <span class="tabular-nums font-bold text-heading w-12 text-right">{{ fmtPct(pct(a.valor)) }}</span>
      </li>
      <li class="flex items-center justify-between px-1.5 pt-1.5 mt-1 border-t border-default text-[11px]">
        <span class="text-muted">Total</span>
        <span class="tabular-nums font-bold text-heading">{{ nf.format(total) }}{{ unidad ? ` ${unidad}` : '' }}</span>
      </li>
    </ul>
  </div>
</template>
