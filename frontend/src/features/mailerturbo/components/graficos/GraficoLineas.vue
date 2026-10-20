<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Table2, ChartLine } from 'lucide-vue-next'
import '../../styles/graficos.css'

// Líneas sobre franjas alternas (una franja por categoría del eje x). Hasta 3
// series con color fijo por posición; la leyenda permite ocultar una sin que las
// demás cambien de color. Hover = resalta la franja + tooltip con todas las series.
/** null = sin dato (p. ej. un día sin envíos): la línea se corta, no cae a 0. */
export interface SerieLineas { id: string; nombre: string; valores: (number | null)[] }
export interface CategoriaLineas { id: string | number; etiqueta: string; titulo?: string; sub?: string }

const props = withDefaults(defineProps<{
  categorias: CategoriaLineas[]
  series: SerieLineas[]
  formato?: 'numero' | 'pct'
  alto?: number
  clicable?: boolean
}>(), { formato: 'numero', alto: 260, clicable: false })
const emit = defineEmits<{ seleccionar: [CategoriaLineas] }>()

const COLORES = ['var(--mt-s1)', 'var(--mt-s2)', 'var(--mt-s3)']
const nf = new Intl.NumberFormat('es-CO')
const fmt = (v: number | null | undefined) => v == null ? '—' : (props.formato === 'pct' ? `${v.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%` : nf.format(Math.round(v)))
const fmtEje = (v: number) => (props.formato === 'pct' ? `${v}%` : v >= 10_000 ? `${nf.format(v / 1000)} k` : nf.format(v))

// ── Tamaño ───────────────────────────────────────────────────────────
const contenedor = ref<HTMLElement | null>(null)
const ancho = ref(600)
let observador: ResizeObserver | undefined
onMounted(() => {
  if (!contenedor.value) return
  observador = new ResizeObserver(([e]) => { ancho.value = Math.max(280, e.contentRect.width) })
  observador.observe(contenedor.value)
})
onBeforeUnmount(() => observador?.disconnect())

const M = { izq: 46, der: 92, arr: 10, aba: 28 }
const plotAncho = computed(() => Math.max(10, ancho.value - M.izq - M.der))
const plotAlto = computed(() => props.alto - M.arr - M.aba)

// ── Series visibles (el color sigue a la serie, no a su posición visible) ──
const ocultas = ref(new Set<string>())
const alternar = (id: string) => {
  const s = new Set(ocultas.value)
  if (s.has(id)) s.delete(id)
  else if (props.series.length - s.size > 1) s.add(id) // siempre queda al menos una
  ocultas.value = s
}
const seriesConColor = computed(() => props.series.slice(0, 3).map((s, i) => ({ ...s, color: COLORES[i] })))
const visibles = computed(() => seriesConColor.value.filter(s => !ocultas.value.has(s.id)))

// ── Escalas ──────────────────────────────────────────────────────────
const n = computed(() => props.categorias.length)
const anchoColumna = computed(() => plotAncho.value / Math.max(1, n.value))
const x = (i: number) => M.izq + anchoColumna.value * (i + 0.5)

const maxY = computed(() => {
  const m = Math.max(0, ...visibles.value.flatMap(s => s.valores.filter((v): v is number => v != null)))
  if (m <= 0) return props.formato === 'pct' ? 10 : 1
  const paso = Math.pow(10, Math.floor(Math.log10(m)))
  const tope = [1, 2, 2.5, 5, 10].map(f => f * paso).find(v => v >= m) ?? 10 * paso
  return props.formato === 'pct' ? Math.min(100, tope) : tope
})
const y = (v: number) => M.arr + plotAlto.value * (1 - v / maxY.value)
const ticks = computed(() => [0, 0.25, 0.5, 0.75, 1].map(f => +(maxY.value * f).toFixed(2)))

// Tramos continuos: cada hueco (null) corta la línea, salvo que se pida unirlos.
const hayHuecos = computed(() => props.series.some(s => s.valores.slice(0, n.value).some(v => v == null)))
const unirHuecos = ref(false)
const ruta = (valores: (number | null)[]) => {
  let d = ''
  let previoNulo = true
  valores.slice(0, n.value).forEach((v, i) => {
    if (v == null) { if (!unirHuecos.value) previoNulo = true; return }
    d += `${previoNulo ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)} `
    previoNulo = false
  })
  return d
}
// Puntos con dato: con huecos se marcan todos (si no, los sueltos ni se verían).
const marcados = (valores: (number | null)[]) =>
  hayHuecos.value || n.value === 1
    ? valores.slice(0, n.value).flatMap((v, i) => (v != null ? [{ i, v }] : []))
    : []
const ultimo = (valores: (number | null)[]) => {
  for (let i = Math.min(valores.length, n.value) - 1; i >= 0; i--) if (valores[i] != null) return valores[i] as number
  return null
}

// Etiquetas del eje x sin choques: como mucho una cada ~64px.
const cadaX = computed(() => Math.max(1, Math.ceil(64 / anchoColumna.value)))

// Etiquetas directas al final de cada línea, separadas si se pisan.
const etiquetasFinales = computed(() => {
  if (!n.value) return []
  const items = visibles.value.flatMap(s => {
    const v = ultimo(s.valores)
    return v == null ? [] : [{ id: s.id, nombre: s.nombre, color: s.color, valor: v, y: y(v) }]
  })
  items.sort((a, b) => a.y - b.y)
  for (let i = 1; i < items.length; i++) if (items[i].y - items[i - 1].y < 14) items[i].y = items[i - 1].y + 14
  // Si se salen por abajo, se reacomodan desde el fondo hacia arriba.
  const fondo = M.arr + plotAlto.value
  for (let i = items.length - 1; i >= 0; i--) {
    const tope = i === items.length - 1 ? fondo : items[i + 1].y - 14
    if (items[i].y > tope) items[i].y = tope
  }
  return items
})

// ── Hover / teclado ──────────────────────────────────────────────────
const hover = ref<number | null>(null)
function moverTeclado(e: KeyboardEvent) {
  if (!n.value) return
  if (e.key === 'ArrowRight') hover.value = Math.min(n.value - 1, (hover.value ?? -1) + 1)
  else if (e.key === 'ArrowLeft') hover.value = Math.max(0, (hover.value ?? n.value) - 1)
  else if (e.key === 'Enter' && hover.value !== null && props.clicable) emit('seleccionar', props.categorias[hover.value])
  else return
  e.preventDefault()
}
const tooltipIzq = computed(() => {
  if (hover.value === null) return 0
  return Math.min(Math.max(x(hover.value), 90), ancho.value - 90)
})

const verTabla = ref(false)
</script>

<template>
  <div class="mt-viz">
    <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
      <!-- Leyenda (clic = mostrar/ocultar la serie) -->
      <div class="flex flex-wrap items-center gap-1">
        <button
          v-for="s in seriesConColor"
          :key="s.id"
          type="button"
          class="flex items-center gap-1.5 h-6 px-2 rounded-md text-[11px] font-semibold transition-opacity hover:bg-slate-50 dark:hover:bg-slate-700/50"
          :class="ocultas.has(s.id) ? 'opacity-40 line-through text-muted' : 'text-body'"
          :aria-pressed="!ocultas.has(s.id)"
          :title="ocultas.has(s.id) ? 'Mostrar' : 'Ocultar'"
          @click="alternar(s.id)"
        >
          <span class="w-3.5 h-[3px] rounded-full" :style="{ background: s.color }" /> {{ s.nombre }}
        </button>
      </div>
      <div class="flex items-center gap-2">
      <label v-if="hayHuecos && !verTabla" class="flex items-center gap-1.5 text-[11px] text-muted cursor-pointer" title="Une los puntos saltando los periodos sin envíos (no inventa datos: solo facilita ver la tendencia)">
        <input v-model="unirHuecos" type="checkbox" class="accent-[#2447F9]" /> Unir huecos
      </label>
      <button
        type="button"
        class="flex items-center gap-1 h-6 px-2 rounded-md text-[11px] font-semibold text-muted hover:text-heading hover:bg-slate-50 dark:hover:bg-slate-700/50"
        @click="verTabla = !verTabla"
      >
        <component :is="verTabla ? ChartLine : Table2" :size="12" /> {{ verTabla ? 'Ver gráfica' : 'Ver tabla' }}
      </button>
      </div>
    </div>

    <!-- Tabla (vista accesible / para copiar los números) -->
    <div v-if="verTabla" class="overflow-auto rounded-lg border border-default" :style="{ maxHeight: `${alto}px` }">
      <table class="w-full text-[11px]">
        <thead class="sticky top-0 bg-white dark:bg-slate-800">
          <tr class="text-left text-[10px] uppercase tracking-wide text-subtle border-b border-default">
            <th class="px-3 py-2 font-semibold">&nbsp;</th>
            <th v-for="s in seriesConColor" :key="s.id" class="px-3 py-2 font-semibold text-right">{{ s.nombre }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(c, i) in categorias" :key="c.id" class="border-b border-slate-100 dark:border-slate-700/60">
            <td class="px-3 py-1.5 text-body">{{ c.titulo ?? c.etiqueta }}<span v-if="c.sub" class="text-muted"> · {{ c.sub }}</span></td>
            <td v-for="s in seriesConColor" :key="s.id" class="px-3 py-1.5 text-right tabular-nums text-heading">{{ fmt(s.valores[i]) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="!verTabla" ref="contenedor" class="relative">
      <p v-if="!categorias.length" class="flex items-center justify-center text-[12px] text-muted" :style="{ height: `${alto}px` }">Sin datos para graficar.</p>
      <svg
        v-else
        :width="ancho"
        :height="alto"
        class="block select-none outline-none focus-visible:ring-2 focus-visible:ring-[#2447F9]/60 rounded-lg"
        role="img"
        :aria-label="`Gráfica de líneas: ${seriesConColor.map(s => s.nombre).join(', ')}. Use las flechas para recorrer los puntos.`"
        tabindex="0"
        @keydown="moverTeclado"
        @mouseleave="hover = null"
        @blur="hover = null"
      >
        <!-- franjas alternas (con 2px de separación del color de la superficie) -->
        <rect
          v-for="(c, i) in categorias"
          :key="`f-${c.id}`"
          :x="M.izq + anchoColumna * i + 1"
          :y="M.arr"
          :width="Math.max(0, anchoColumna - 2)"
          :height="plotAlto"
          :fill="i % 2 ? 'var(--mt-franja-b)' : 'var(--mt-franja-a)'"
        />
        <rect
          v-if="hover !== null"
          :x="M.izq + anchoColumna * hover + 1"
          :y="M.arr"
          :width="Math.max(0, anchoColumna - 2)"
          :height="plotAlto"
          fill="var(--mt-eje)"
          opacity="0.45"
        />

        <!-- guías horizontales (del color de la superficie, como en las franjas) -->
        <g>
          <template v-for="t in ticks" :key="`t-${t}`">
            <line :x1="M.izq" :x2="M.izq + plotAncho" :y1="y(t)" :y2="y(t)" stroke="var(--mt-superficie)" stroke-width="1" />
            <text :x="M.izq - 6" :y="y(t)" text-anchor="end" dominant-baseline="middle" class="fill-slate-400 dark:fill-slate-500" font-size="10">{{ fmtEje(t) }}</text>
          </template>
        </g>

        <!-- eje x -->
        <template v-for="(c, i) in categorias" :key="`x-${c.id}`">
          <text
            v-if="i % cadaX === 0 || i === n - 1"
            :x="x(i)"
            :y="alto - 9"
            text-anchor="middle"
            font-size="10"
            :class="hover === i ? 'fill-slate-700 dark:fill-slate-200 font-semibold' : 'fill-slate-400 dark:fill-slate-500'"
          >{{ c.etiqueta }}</text>
        </template>

        <!-- líneas -->
        <path
          v-for="s in visibles"
          :key="`l-${s.id}`"
          :d="ruta(s.valores)"
          fill="none"
          :stroke="s.color"
          stroke-width="2"
          stroke-linejoin="round"
          stroke-linecap="round"
        />
        <!-- puntos con dato cuando hay huecos -->
        <template v-for="s in visibles" :key="`p-${s.id}`">
          <circle v-for="p in marcados(s.valores)" :key="p.i" :cx="x(p.i)" :cy="y(p.v)" r="4.5" :fill="s.color" stroke="var(--mt-superficie)" stroke-width="2" />
        </template>

        <!-- marcadores del punto con hover -->
        <template v-if="hover !== null">
          <circle
            v-for="s in visibles.filter(s => s.valores[hover!] != null)"
            :key="`h-${s.id}`"
            :cx="x(hover)"
            :cy="y(s.valores[hover] ?? 0)"
            r="4.5"
            :fill="s.color"
            stroke="var(--mt-superficie)"
            stroke-width="2"
          />
        </template>

        <!-- etiquetas directas al final -->
        <g v-for="e in etiquetasFinales" :key="`e-${e.id}`">
          <text :x="M.izq + plotAncho + 8" :y="e.y" dominant-baseline="middle" font-size="10.5" font-weight="600" class="fill-slate-700 dark:fill-slate-200">
            <tspan :fill="e.color">●</tspan> {{ e.nombre }}
          </text>
        </g>

        <!-- zonas de hover (una por columna, más grandes que la marca) -->
        <rect
          v-for="(c, i) in categorias"
          :key="`z-${c.id}`"
          :x="M.izq + anchoColumna * i"
          :y="0"
          :width="anchoColumna"
          :height="alto"
          fill="transparent"
          :class="clicable ? 'cursor-pointer' : ''"
          @mouseenter="hover = i"
          @click="clicable && emit('seleccionar', c)"
        />
      </svg>

      <div
        v-if="hover !== null && categorias[hover]"
        class="mt-tooltip"
        :style="{ left: `${tooltipIzq}px`, top: `${M.arr + 4}px`, transform: 'translate(-50%, 0)' }"
      >
        <div class="font-bold">{{ categorias[hover].titulo ?? categorias[hover].etiqueta }}</div>
        <div v-if="categorias[hover].sub" class="opacity-70 mb-1">{{ categorias[hover].sub }}</div>
        <div v-for="s in visibles" :key="`tt-${s.id}`" class="flex items-center justify-between gap-4">
          <span class="flex items-center gap-1.5"><span class="w-2.5 h-[3px] rounded-full" :style="{ background: s.color }" />{{ s.nombre }}</span>
          <strong class="tabular-nums">{{ s.valores[hover] == null ? 'sin envíos' : fmt(s.valores[hover]) }}</strong>
        </div>
        <div v-if="clicable" class="opacity-60 mt-1">Clic para ver el detalle</div>
      </div>
    </div>
  </div>
</template>
