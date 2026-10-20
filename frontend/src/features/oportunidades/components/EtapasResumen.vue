<script setup lang="ts">
import type { EtapaOportunidad, Oportunidad } from '../types/oportunidad'

defineProps<{
  etapas: EtapaOportunidad[]
  oportunidades: Oportunidad[]
  filtroEstado: string
}>()
const emit = defineEmits<{ 'toggle-etapa': [etapa: EtapaOportunidad] }>()
</script>

<template>
  <div class="grid grid-cols-3 sm:grid-cols-5 xl:grid-cols-7 gap-3">
    <div
      v-for="etapa in etapas"
      :key="etapa"
      class="surface-card rounded-xl shadow-sm p-3 text-center cursor-pointer hover:border-[#2447F9] transition-all"
      :class="filtroEstado === etapa ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40' : ''"
      @click="emit('toggle-etapa', etapa)"
    >
      <div class="text-[20px] font-bold" :class="filtroEstado === etapa ? 'text-slate-900 font-bold' : 'text-heading'">
        {{ oportunidades.filter(o => o.estado === etapa).length }}
      </div>
      <div class="text-[9px] font-bold text-subtle uppercase tracking-wide mt-0.5 truncate">{{ etapa }}</div>
    </div>
  </div>
</template>
