<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import '../../styles/graficos.css'
import { intervalos, media, desviacion, cuantil, normalPdf } from '../../utils/estadistica'

// Histograma (intervalos por Sturges) con la campana de Gauss ajustada a la media y
// la desviación de los datos, escalada a frecuencias (n × ancho × densidad) para
// compartir el mismo eje. Líneas verticales: media y mediana.
export interface DatoHistograma { id: string | number; label: string; valor: number }
const props = withDefaults(defineProps<{ datos: DatoHistograma[]; formato?: 'pct' | 'numero'; alto?: number; unidad?: string }>(), {
  formato: 'pct', alto: 260, unidad: 'campañas',
})

const nf = new Intl.NumberFormat('es-CO')
const fmt = (v: number) => (props.formato === 'pct' ? `${v.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%` : nf.format(Math.round(v)))
const verGauss = ref(true)

const contenedor = ref<HTMLElement | null>(null)
const ancho = ref(600)
let observador: ResizeObserver | undefined
onMounted(() => {
  if (!contenedor.value) return
  observador = new ResizeObserver(([e]) => { ancho.value = Math.max(280, e.contentRect.width) })
  observador.observe(contenedor.value)
})
onBeforeUnmount(() => observador?.disconnect())

const M = { izq: 34, der: 12, arr: 22, aba: 30 }
const valores = computed(() => props.datos.map(d => d.valor))
const m = computed(() => media(valores.value))
const s = computed(() => desviacion(valores.value))
const mediana = computed(() => cuantil(valores.value, 0.5))

const cubos = computed(() =>
  intervalos(valores.value).map((b, i, arr) => ({
    ...b,
    // El último intervalo incluye su límite superior.
    items: props.datos.filter(d => d.valor >= b.desde && (d.valor < b.hasta || (i === arr.length - 1 && d.valor <= b.hasta))),
  })),
)
const anchoIntervalo = computed(() => (cubos.value[0] ? cubos.value[0].hasta - cubos.value[0].desde : 1))

// Dominio x: los intervalos, ampliado a media ± 3σ para que se vea la campana entera
// (sin salir de 0–100 en porcentajes ni de 0 en cantidades).
const dominio = computed(() => {
  if (!cubos.value.length) return [0, 1]
  let a = cubos.value[0].desde, b = cubos.value[cubos.value.length - 1].hasta
  if (verGauss.value && s.value > 0) { a = Math.min(a, m.value - 3 * s.value); b = Math.max(b, m.value + 3 * s.value) }
  a = Math.max(0, a)
  if (props.formato === 'pct') b = Math.min(100, Math.max(b, cubos.value[cubos.value.length - 1].hasta))
  return [a, b]
})
const plotW = computed(() => ancho.value - M.izq - M.der)
const plotH = computed(() => props.alto - M.arr - M.aba)
const x = (v: number) => M.izq + ((v - dominio.value[0]) / (dominio.value[1] - dominio.value[0] || 1)) * plotW.value

const gauss = computed(() => {
  if (!verGauss.value || !(s.value > 0)) return []
  const [a, b] = dominio.value
  const n = props.datos.length
  return Array.from({ length: 121 }, (_, i) => {
    const v = a + ((b - a) * i) / 120
    return { v, f: n * anchoIntervalo.value * normalPdf(v, m.value, s.value) }
  })
})
const maxY = computed(() => {
  const mx = Math.max(1, ...cubos.value.map(c => c.items.length), ...gauss.value.map(g => g.f))
  return Math.ceil(mx)
})
const y = (f: number) => M.arr + plotH.value * (1 - f / maxY.value)
const ticksY = computed(() => {
  const paso = Math.max(1, Math.ceil(maxY.value / 4))
  const r: number[] = []
  for (let t = 0; t <= maxY.value; t += paso) r.push(t)
  return r
})
const rutaGauss = computed(() => gauss.value.map((g, i) => `${i ? 'L' : 'M'}${x(g.v).toFixed(1)},${y(g.f).toFixed(1)}`).join(' '))
const ticksX = computed(() => {
  const [a, b] = dominio.value
  const paso = anchoIntervalo.value * Math.max(1, Math.ceil(((b - a) / anchoIntervalo.value) / Math.max(2, Math.floor(plotW.value / 70))))
  const r: number[] = []
  for (let t = Math.ceil(a / paso) * paso; t <= b + 1e-9; t += paso) r.push(+t.toFixed(6))
  return r
})

const hover = ref<number | null>(null)
</script>

<template>
  <div class="mt-viz">
    <div class="flex flex-wrap items-center justify-between gap-2 mb-1 text-[11px]">
      <div class="flex flex-wrap items-center gap-3 text-body">
        <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm" style="background: var(--mt-s1)" /> Campañas por intervalo</span>
        <span v-if="verGauss && s > 0" class="flex items-center gap-1.5"><span class="w-3.5 h-[3px] rounded-full" style="background: var(--mt-s2)" /> Campana de Gauss</span>
        <span class="flex items-center gap-1.5"><span class="w-[2px] h-3 bg-slate-800 dark:bg-slate-100" /> Media</span>
        <span class="flex items-center gap-1.5"><span class="w-[2px] h-3" style="background: var(--mt-s3)" /> Mediana</span>
      </div>
      <label class="flex items-center gap-1.5 text-muted cursor-pointer">
        <input v-model="verGauss" type="checkbox" class="accent-[#2447F9]" /> Mostrar campana de Gauss
      </label>
    </div>

    <div ref="contenedor" class="relative">
      <p v-if="datos.length < 2" class="flex items-center justify-center text-[12px] text-muted" :style="{ height: `${alto}px` }">Se necesitan al menos 2 campañas.</p>
      <svg v-else :width="ancho" :height="alto" class="block" role="img" :aria-label="`Histograma de ${datos.length} campañas, media ${fmt(m)}, mediana ${fmt(mediana)}`" @mouseleave="hover = null">
        <!-- guías -->
        <template v-for="t in ticksY" :key="`gy-${t}`">
          <line :x1="M.izq" :x2="M.izq + plotW" :y1="y(t)" :y2="y(t)" stroke="var(--mt-grid)" />
          <text :x="M.izq - 6" :y="y(t)" text-anchor="end" dominant-baseline="middle" font-size="10" class="fill-slate-400 dark:fill-slate-500">{{ t }}</text>
        </template>
        <!-- ±1σ (68% teórico) -->
        <rect v-if="verGauss && s > 0" :x="x(Math.max(dominio[0], m - s))" :y="M.arr" :width="Math.max(0, x(Math.min(dominio[1], m + s)) - x(Math.max(dominio[0], m - s)))" :height="plotH" fill="var(--mt-s2)" opacity="0.07" />
        <!-- barras -->
        <g v-for="(c, i) in cubos" :key="`b-${i}`">
          <rect
            :x="x(c.desde) + 1"
            :y="y(c.items.length)"
            :width="Math.max(0, x(c.hasta) - x(c.desde) - 2)"
            :height="Math.max(0, y(0) - y(c.items.length))"
            rx="3"
            fill="var(--mt-s1)"
            :opacity="hover === null || hover === i ? 0.85 : 0.4"
          />
          <text v-if="c.items.length" :x="(x(c.desde) + x(c.hasta)) / 2" :y="y(c.items.length) - 4" text-anchor="middle" font-size="10" font-weight="600" class="fill-slate-600 dark:fill-slate-300">{{ c.items.length }}</text>
          <rect :x="x(c.desde)" :y="M.arr" :width="Math.max(0, x(c.hasta) - x(c.desde))" :height="plotH" fill="transparent" @mouseenter="hover = i" />
        </g>
        <!-- eje x -->
        <line :x1="M.izq" :x2="M.izq + plotW" :y1="y(0)" :y2="y(0)" stroke="var(--mt-eje)" />
        <text v-for="t in ticksX" :key="`tx-${t}`" :x="x(t)" :y="alto - 12" text-anchor="middle" font-size="10" class="fill-slate-400 dark:fill-slate-500">{{ fmt(t) }}</text>
        <!-- Gauss -->
        <path v-if="gauss.length" :d="rutaGauss" fill="none" stroke="var(--mt-s2)" stroke-width="2" stroke-linejoin="round" pointer-events="none" />
        <!-- media y mediana -->
        <g pointer-events="none">
          <line :x1="x(m)" :x2="x(m)" :y1="M.arr - 4" :y2="y(0)" class="stroke-slate-800 dark:stroke-slate-100" stroke-width="1.5" />
          <text :x="x(m)" :y="M.arr - 8" text-anchor="middle" font-size="10" font-weight="700" class="fill-slate-800 dark:fill-slate-100">x̄ {{ fmt(m) }}</text>
          <line :x1="x(mediana)" :x2="x(mediana)" :y1="M.arr + 10" :y2="y(0)" stroke="var(--mt-s3)" stroke-width="1.5" />
          <text :x="x(mediana) + (mediana < m ? -4 : 4)" :y="M.arr + 6" :text-anchor="mediana < m ? 'end' : 'start'" font-size="10" font-weight="700" fill="var(--mt-s3)">Me {{ fmt(mediana) }}</text>
        </g>
      </svg>
      <div v-if="hover !== null && cubos[hover]" class="mt-tooltip" :style="{ left: `${Math.min(Math.max(x((cubos[hover].desde + cubos[hover].hasta) / 2), 110), ancho - 110)}px`, top: `${M.arr}px`, transform: 'translate(-50%, 0)', whiteSpace: 'normal', width: '220px' }">
        <strong>{{ fmt(cubos[hover].desde) }} – {{ fmt(cubos[hover].hasta) }}</strong> · {{ cubos[hover].items.length }} {{ unidad }}
        <div v-for="it in cubos[hover].items.slice(0, 6)" :key="it.id" class="opacity-80 truncate">· {{ it.label }} ({{ fmt(it.valor) }})</div>
        <div v-if="cubos[hover].items.length > 6" class="opacity-60">y {{ cubos[hover].items.length - 6 }} más…</div>
      </div>
    </div>
  </div>
</template>
