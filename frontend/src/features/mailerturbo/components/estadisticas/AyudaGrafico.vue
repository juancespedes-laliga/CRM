<script setup lang="ts">
import { ref } from 'vue'
import { CircleHelp, ChevronDown } from 'lucide-vue-next'

// Explicación desplegable, en lenguaje sencillo, de cómo leer y usar una gráfica.
// Cerrada por defecto para no recargar la vista.
withDefaults(defineProps<{ titulo?: string }>(), { titulo: '¿Cómo leer esto?' })
const abierta = ref(false)
</script>

<template>
  <div class="mb-3">
    <button
      type="button"
      class="inline-flex items-center gap-1 text-[11px] font-semibold text-[#2447F9] dark:text-blue-300 hover:underline"
      :aria-expanded="abierta"
      @click="abierta = !abierta"
    >
      <CircleHelp :size="12" /> {{ titulo }}
      <ChevronDown :size="12" class="transition-transform" :class="{ 'rotate-180': abierta }" />
    </button>
    <div
      v-if="abierta"
      class="mt-2 rounded-xl border border-blue-100 dark:border-slate-600 bg-blue-50/60 dark:bg-slate-700/40 px-3.5 py-3 text-[12px] leading-relaxed text-body space-y-1.5 [&_strong]:text-heading [&_ul]:list-disc [&_ul]:pl-4 [&_ul]:space-y-1"
    >
      <slot />
    </div>
  </div>
</template>
