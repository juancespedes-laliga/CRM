<script setup lang="ts">
import { CUPO_MAXIMO } from '../constants/plan-liga.constants'

const props = withDefaults(defineProps<{
  activos: number
  max?: number
  variant?: 'dots' | 'bar'
}>(), { variant: 'dots', max: CUPO_MAXIMO })
</script>

<template>
  <!--
    flex-wrap + max-w acotado: con el cambio de plan al renovar, un titular puede
    terminar con un cupo bastante mayor al Estándar (6, 8...). Sin el wrap, los puntos
    se salían del ancho de la celda en la tabla y quedaban tapando la columna siguiente
    (Inscripción) en vez de acomodarse en una segunda fila. w-full + overflow-hidden:
    red de seguridad para que el contenedor nunca sea más ancho que el espacio real
    que le da el padre (la fila completa ya no se ensancha por el número al lado,
    porque el número ahora va aparte, ver TitularesTable.vue).
  -->
  <div v-if="variant === 'dots'" class="flex flex-wrap gap-0.5 w-full max-w-[90px] overflow-hidden">
    <div v-for="slot in props.max" :key="slot" class="w-3.5 h-3.5 rounded-sm border transition-all shrink-0"
      :class="slot <= activos ? 'bg-[#EC4899] border-[#EC4899]' : 'bg-slate-100 dark:bg-slate-700 border-slate-200 dark:border-slate-600'" />
  </div>
  <div v-else class="flex gap-2">
    <div v-for="slot in props.max" :key="slot" class="flex-1 h-2.5 rounded-full transition-all" :class="slot <= activos ? 'bg-[#EC4899]' : 'bg-slate-100 dark:bg-slate-700'" />
  </div>
</template>
