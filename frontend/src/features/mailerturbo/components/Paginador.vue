<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-vue-next'

// Paginador con números de página, "x–y de N" y selector de filas por página.
const props = withDefaults(defineProps<{
  pagina: number
  totalPaginas: number
  total?: number
  porPagina?: number
  opcionesPorPagina?: number[]
  deshabilitado?: boolean
}>(), { opcionesPorPagina: () => [10, 25, 50, 100] })

const emit = defineEmits<{ 'update:pagina': [number]; 'update:porPagina': [number] }>()
const nf = new Intl.NumberFormat('es-CO')

const ir = (p: number) => {
  const destino = Math.min(Math.max(1, p), Math.max(1, props.totalPaginas))
  if (destino !== props.pagina) emit('update:pagina', destino)
}

// 1 … 4 5 [6] 7 8 … 20
const numeros = computed<(number | '…')[]>(() => {
  const total = Math.max(1, props.totalPaginas)
  const actual = props.pagina
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const desde = Math.max(2, actual - 1)
  const hasta = Math.min(total - 1, actual + 1)
  const r: (number | '…')[] = [1]
  if (desde > 2) r.push('…')
  for (let p = desde; p <= hasta; p++) r.push(p)
  if (hasta < total - 1) r.push('…')
  r.push(total)
  return r
})

const rango = computed(() => {
  if (props.total == null || !props.porPagina) return null
  if (!props.total) return '0 resultados'
  const desde = (props.pagina - 1) * props.porPagina + 1
  const hasta = Math.min(props.total, props.pagina * props.porPagina)
  return `${nf.format(desde)}–${nf.format(hasta)} de ${nf.format(props.total)}`
})

const btn = 'min-w-7 h-7 px-1.5 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-white dark:disabled:hover:bg-slate-800'
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted">
    <div class="flex items-center gap-3">
      <span v-if="rango" class="tabular-nums">{{ rango }}</span>
      <label v-if="porPagina && opcionesPorPagina.length" class="flex items-center gap-1.5">
        Filas
        <select
          :value="porPagina"
          :disabled="deshabilitado"
          class="h-7 px-1.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] text-body outline-none"
          @change="emit('update:porPagina', Number(($event.target as HTMLSelectElement).value))"
        >
          <option v-for="o in opcionesPorPagina" :key="o" :value="o">{{ o }}</option>
        </select>
      </label>
    </div>
    <nav class="flex items-center gap-1" aria-label="Paginación">
      <button :class="btn" :disabled="deshabilitado || pagina <= 1" title="Primera página" @click="ir(1)"><ChevronsLeft :size="13" /></button>
      <button :class="btn" :disabled="deshabilitado || pagina <= 1" title="Anterior" @click="ir(pagina - 1)"><ChevronLeft :size="13" /></button>
      <template v-for="(n, i) in numeros" :key="`${n}-${i}`">
        <span v-if="n === '…'" class="px-1">…</span>
        <button
          v-else
          :class="[btn, n === pagina ? '!bg-[#2447F9] !border-[#2447F9] !text-white' : '']"
          :disabled="deshabilitado"
          :aria-current="n === pagina ? 'page' : undefined"
          @click="ir(n)"
        >{{ n }}</button>
      </template>
      <button :class="btn" :disabled="deshabilitado || pagina >= totalPaginas" title="Siguiente" @click="ir(pagina + 1)"><ChevronRight :size="13" /></button>
      <button :class="btn" :disabled="deshabilitado || pagina >= totalPaginas" title="Última página" @click="ir(totalPaginas)"><ChevronsRight :size="13" /></button>
    </nav>
  </div>
</template>
