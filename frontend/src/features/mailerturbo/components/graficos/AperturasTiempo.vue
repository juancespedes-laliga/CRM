<script setup lang="ts">
import { computed, ref } from 'vue'
import GraficoLineas from './GraficoLineas.vue'

// Cuándo abrieron y cuándo hicieron clic: por hora desde el envío (primeras 48 h)
// o por día. Dos series de la misma unidad (personas) sobre un solo eje.
const props = defineProps<{ inicio: string | null; aperturas: string[]; clics: string[] }>()

const nf = new Intl.NumberFormat('es-CO')
const modo = ref<'hora' | 'dia'>('hora')
const HORAS = 48
const MAX_DIAS = 30

const aFecha = (s: string) => new Date(s.replace(' ', 'T'))
const t0 = computed(() => {
  if (props.inicio) return aFecha(props.inicio).getTime()
  const ts = props.aperturas.map(a => aFecha(a).getTime())
  return ts.length ? Math.min(...ts) : 0
})
const inicioDia = computed(() => { const d = new Date(t0.value); d.setHours(0, 0, 0, 0); return d })
const horasDesde = (fechas: string[]) =>
  fechas.map(a => (aFecha(a).getTime() - t0.value) / 3_600_000).filter(h => h >= 0).sort((a, b) => a - b)

const dias = computed(() => {
  const ultima = Math.max(0, ...horasDesde(props.aperturas))
  const offset = (t0.value - inicioDia.value.getTime()) / 3_600_000
  return Math.min(MAX_DIAS, Math.max(7, Math.ceil((offset + ultima) / 24)))
})

function contar(fechas: string[]) {
  if (modo.value === 'hora') {
    const cubos = new Array<number>(HORAS).fill(0)
    let fuera = 0
    for (const h of horasDesde(fechas)) { if (h < HORAS) cubos[Math.floor(h)]++; else fuera++ }
    return { cubos, fuera }
  }
  const cubos = new Array<number>(dias.value).fill(0)
  let fuera = 0
  for (const f of fechas) {
    const i = Math.floor((aFecha(f).getTime() - inicioDia.value.getTime()) / 86_400_000)
    if (i >= 0 && i < dias.value) cubos[i]++
    else if (i >= dias.value) fuera++
  }
  return { cubos, fuera }
}

const categorias = computed(() => {
  if (modo.value === 'hora') {
    return Array.from({ length: HORAS }, (_, i) => ({ id: i, etiqueta: `${i} h`, titulo: `Entre la hora ${i} y la ${i + 1} desde el envío` }))
  }
  return Array.from({ length: dias.value }, (_, i) => {
    const d = new Date(inicioDia.value); d.setDate(d.getDate() + i)
    return {
      id: i,
      etiqueta: d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' }),
      titulo: d.toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' }),
    }
  })
})
const aperturas = computed(() => contar(props.aperturas))
const clics = computed(() => contar(props.clics))
const series = computed(() => [
  { id: 'aperturas', nombre: 'Aperturas', valores: aperturas.value.cubos },
  { id: 'clics', nombre: 'Clics', valores: clics.value.cubos },
])
const fuera = computed(() => {
  const n = aperturas.value.fuera
  if (!n) return ''
  return modo.value === 'hora' ? `${nf.format(n)} aperturas después de 48 h` : `${nf.format(n)} aperturas después del día ${dias.value}`
})

// Titular: en cuánto tiempo ocurrió la mitad de las aperturas.
const mediana = computed(() => {
  const h = horasDesde(props.aperturas)
  if (!h.length) return null
  const m = h[Math.floor(h.length / 2)]
  return m < 1 ? `${Math.max(1, Math.round(m * 60))} min` : m < 48 ? `${m.toFixed(m < 10 ? 1 : 0)} h` : `${(m / 24).toFixed(1)} días`
})
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
      <p class="text-[11px] text-muted">
        <template v-if="mediana">La mitad de las aperturas ocurrió en las primeras <strong class="text-heading">{{ mediana }}</strong>.</template>
        <template v-else>Aún no hay aperturas.</template>
      </p>
      <div class="flex rounded-lg border border-default p-0.5 text-[11px] font-semibold" role="tablist">
        <button v-for="m in (['hora', 'dia'] as const)" :key="m" type="button" role="tab" :aria-selected="modo === m"
          class="h-6 px-2.5 rounded-md transition-colors"
          :class="modo === m ? 'bg-[#2447F9] text-white' : 'text-muted hover:text-heading'"
          @click="modo = m">{{ m === 'hora' ? 'Por hora (48 h)' : 'Por día' }}</button>
      </div>
    </div>
    <GraficoLineas :categorias="categorias" :series="series" :alto="230" />
    <p v-if="fuera" class="text-[10px] text-muted mt-1">+ {{ fuera }}</p>
  </div>
</template>
