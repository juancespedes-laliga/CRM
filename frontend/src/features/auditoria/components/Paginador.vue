<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps<{ total: number; porPagina: number }>()
const pagina = defineModel<number>({ required: true })

const paginas = computed(() => Math.max(1, Math.ceil(props.total / props.porPagina)))
const desde = computed(() => (props.total === 0 ? 0 : (pagina.value - 1) * props.porPagina + 1))
const hasta = computed(() => Math.min(props.total, pagina.value * props.porPagina))

const ir = (p: number) => { pagina.value = Math.min(paginas.value, Math.max(1, p)) }
</script>

<template>
  <div v-if="total > porPagina" class="flex items-center justify-between gap-3 px-1 text-[11px] text-muted">
    <span>{{ desde }}–{{ hasta }} de <strong class="text-body">{{ total.toLocaleString('es-CO') }}</strong></span>
    <div class="flex items-center gap-1">
      <button type="button" :disabled="pagina <= 1" @click="ir(pagina - 1)" aria-label="Página anterior"
        class="w-7 h-7 rounded-lg border border-default surface-card flex items-center justify-center text-body surface-hover disabled:opacity-40 disabled:cursor-not-allowed">
        <ChevronLeft :size="13" />
      </button>
      <span class="px-2 font-semibold text-body tabular-nums">{{ pagina }} / {{ paginas }}</span>
      <button type="button" :disabled="pagina >= paginas" @click="ir(pagina + 1)" aria-label="Página siguiente"
        class="w-7 h-7 rounded-lg border border-default surface-card flex items-center justify-center text-body surface-hover disabled:opacity-40 disabled:cursor-not-allowed">
        <ChevronRight :size="13" />
      </button>
    </div>
  </div>
</template>
