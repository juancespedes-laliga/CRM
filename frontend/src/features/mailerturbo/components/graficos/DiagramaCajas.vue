<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import '../../styles/graficos.css'
import { resumen, esAtipico, type Resumen5 } from '../../utils/estadistica'

// Diagrama de cajas de Tukey, horizontal, un grupo por fila sobre la misma escala:
// caja = Q1–Q3, raya gruesa = mediana, rombo = media, bigotes = dato más extremo
// dentro de 1,5 × IQR. Cada campaña es un punto; los atípicos van con anillo.
export interface DatoCaja { id: string | number; label: string; valor: number }
export interface GrupoCaja { id: string | number; label: string; datos: DatoCaja[] }
const props = withDefaults(defineProps<{ grupos: GrupoCaja[]; formato?: 'pct' | 'numero' }>(), { formato: 'pct' })
const emit = defineEmits<{ seleccionar: [DatoCaja] }>()

const nf = new Intl.NumberFormat('es-CO')
const fmt = (v: number) => (Number.isNaN(v) ? '—' : props.formato === 'pct' ? `${v.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%` : nf.format(Math.round(v)))

const contenedor = ref<HTMLElement | null>(null)
const ancho = ref(600)
let observador: ResizeObserver | undefined
onMounted(() => {
  if (!contenedor.value) return
  observador = new ResizeObserver(([e]) => { ancho.value = Math.max(280, e.contentRect.width) })
  observador.observe(contenedor.value)
})
onBeforeUnmount(() => observador?.disconnect())

const FILA = 46
const M = { izq: 92, der: 16, arr: 6, aba: 26 }
const filas = computed(() =>
  props.grupos.filter(g => g.datos.length).map(g => ({ ...g, r: resumen(g.datos.map(d => d.valor)) as Resumen5 })),
)
const alto = computed(() => M.arr + filas.value.length * FILA + M.aba)
const plotW = computed(() => ancho.value - M.izq - M.der)

const dominio = computed(() => {
  const vs = filas.value.flatMap(f => f.datos.map(d => d.valor))
  if (!vs.length) return [0, 1]
  const a = Math.min(...vs), b = Math.max(...vs)
  const pad = (b - a || Math.abs(b) || 1) * 0.06
  return [Math.max(0, a - pad), props.formato === 'pct' ? Math.min(100, b + pad) : b + pad]
})
const x = (v: number) => M.izq + ((v - dominio.value[0]) / (dominio.value[1] - dominio.value[0] || 1)) * plotW.value
const ticks = computed(() => {
  const [a, b] = dominio.value
  const crudo = (b - a) / Math.max(2, Math.floor(plotW.value / 80))
  const mag = Math.pow(10, Math.floor(Math.log10(crudo || 1)))
  const paso = [1, 2, 2.5, 5, 10].map(f => f * mag).find(v => v >= crudo) ?? 10 * mag
  const r: number[] = []
  for (let t = Math.ceil(a / paso) * paso; t <= b + 1e-9; t += paso) r.push(+t.toFixed(6))
  return r
})
const yFila = (i: number) => M.arr + i * FILA + FILA / 2
// Dispersión vertical determinista (los puntos no saltan al redibujar).
const jitter = (j: number) => (((j * 9301 + 49297) % 233280) / 233280 - 0.5) * 14

const hover = ref<number | null>(null)
const hoverPunto = ref<{ fila: number; dato: DatoCaja } | null>(null)
</script>

<template>
  <div ref="contenedor" class="mt-viz relative">
    <p v-if="!filas.length" class="py-10 text-center text-[12px] text-muted">Sin datos.</p>
    <svg v-else :width="ancho" :height="alto" class="block" role="img" aria-label="Diagrama de cajas" @mouseleave="hover = null; hoverPunto = null">
      <template v-for="t in ticks" :key="`t-${t}`">
        <line :x1="x(t)" :x2="x(t)" :y1="M.arr" :y2="alto - M.aba" stroke="var(--mt-grid)" />
        <text :x="x(t)" :y="alto - 9" text-anchor="middle" font-size="10" class="fill-slate-400 dark:fill-slate-500">{{ fmt(t) }}</text>
      </template>

      <g v-for="(f, i) in filas" :key="f.id">
        <rect :x="0" :y="yFila(i) - FILA / 2" :width="ancho" :height="FILA" :fill="hover === i ? 'var(--mt-pista)' : 'transparent'" @mouseenter="hover = i" />
        <text :x="M.izq - 10" :y="yFila(i) - 3" text-anchor="end" font-size="11" font-weight="600" class="fill-slate-700 dark:fill-slate-200" pointer-events="none">{{ f.label }}</text>
        <text :x="M.izq - 10" :y="yFila(i) + 10" text-anchor="end" font-size="9.5" class="fill-slate-400 dark:fill-slate-500" pointer-events="none">n = {{ f.r.n }}</text>
        <g pointer-events="none">
          <!-- bigotes -->
          <line :x1="x(f.r.bigoteInf)" :x2="x(f.r.q1)" :y1="yFila(i)" :y2="yFila(i)" stroke="var(--mt-s1)" stroke-width="1.5" />
          <line :x1="x(f.r.q3)" :x2="x(f.r.bigoteSup)" :y1="yFila(i)" :y2="yFila(i)" stroke="var(--mt-s1)" stroke-width="1.5" />
          <line :x1="x(f.r.bigoteInf)" :x2="x(f.r.bigoteInf)" :y1="yFila(i) - 7" :y2="yFila(i) + 7" stroke="var(--mt-s1)" stroke-width="1.5" />
          <line :x1="x(f.r.bigoteSup)" :x2="x(f.r.bigoteSup)" :y1="yFila(i) - 7" :y2="yFila(i) + 7" stroke="var(--mt-s1)" stroke-width="1.5" />
          <!-- caja -->
          <rect :x="x(f.r.q1)" :y="yFila(i) - 12" :width="Math.max(2, x(f.r.q3) - x(f.r.q1))" height="24" rx="4" fill="var(--mt-s1)" fill-opacity="0.18" stroke="var(--mt-s1)" stroke-width="1.5" />
          <line :x1="x(f.r.mediana)" :x2="x(f.r.mediana)" :y1="yFila(i) - 12" :y2="yFila(i) + 12" stroke="var(--mt-s1)" stroke-width="3" />
          <!-- media -->
          <path :d="`M${x(f.r.media)},${yFila(i) - 5} l5,5 l-5,5 l-5,-5 Z`" fill="var(--mt-s2)" stroke="var(--mt-superficie)" stroke-width="1.5" />
        </g>
        <!-- puntos -->
        <circle
          v-for="(d, j) in f.datos"
          :key="d.id"
          :cx="x(d.valor)"
          :cy="yFila(i) + jitter(j)"
          :r="esAtipico(d.valor, f.r) ? 4.5 : 3"
          :fill="esAtipico(d.valor, f.r) ? 'var(--mt-s2)' : 'currentColor'"
          :stroke="esAtipico(d.valor, f.r) ? 'var(--mt-superficie)' : 'none'"
          stroke-width="2"
          class="text-slate-500/60 dark:text-slate-300/50 cursor-pointer"
          @mouseenter="hover = i; hoverPunto = { fila: i, dato: d }"
          @mouseleave="hoverPunto = null"
          @click="emit('seleccionar', d)"
        />
      </g>
    </svg>

    <div v-if="hoverPunto" class="mt-tooltip" :style="{ left: `${Math.min(Math.max(x(hoverPunto.dato.valor), 110), ancho - 110)}px`, top: `${yFila(hoverPunto.fila) - 14}px` }">
      <strong>{{ hoverPunto.dato.label }}</strong> · {{ fmt(hoverPunto.dato.valor) }}
      <span v-if="esAtipico(hoverPunto.dato.valor, filas[hoverPunto.fila].r)" class="opacity-80"> · atípico</span>
      <div class="opacity-60">Clic para ver la campaña</div>
    </div>
    <div v-else-if="hover !== null && filas[hover]" class="mt-tooltip" :style="{ left: `${Math.min(Math.max(x(filas[hover].r.mediana), 120), ancho - 120)}px`, top: `${yFila(hover) - 16}px` }">
      <strong>{{ filas[hover].label }}</strong> · n = {{ filas[hover].r.n }}<br />
      Mín {{ fmt(filas[hover].r.min) }} · Q1 {{ fmt(filas[hover].r.q1) }} · Mediana {{ fmt(filas[hover].r.mediana) }}<br />
      Q3 {{ fmt(filas[hover].r.q3) }} · Máx {{ fmt(filas[hover].r.max) }} · Media {{ fmt(filas[hover].r.media) }}
    </div>

    <div class="flex flex-wrap items-center gap-4 mt-2 text-[10.5px] text-muted">
      <span class="flex items-center gap-1.5"><span class="w-4 h-3 rounded-sm border-[1.5px]" style="border-color: var(--mt-s1); background: color-mix(in srgb, var(--mt-s1) 18%, transparent)" /> 50% central (Q1–Q3)</span>
      <span class="flex items-center gap-1.5"><span class="w-[3px] h-3" style="background: var(--mt-s1)" /> Mediana</span>
      <span class="flex items-center gap-1.5"><span class="w-2 h-2 rotate-45" style="background: var(--mt-s2)" /> Media</span>
      <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-slate-400" /> Campaña</span>
      <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full ring-2 ring-white dark:ring-slate-800" style="background: var(--mt-s2)" /> Atípica (fuera de 1,5 × IQR)</span>
    </div>
  </div>
</template>
