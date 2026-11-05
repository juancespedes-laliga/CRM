<script setup lang="ts">
import { History, RefreshCw } from 'lucide-vue-next'
import type { TabAuditoria } from '../types/auditoria'

defineProps<{ renovacionesDisponible: boolean }>()
const tab = defineModel<TabAuditoria>({ required: true })

const clase = (activa: boolean) => activa
  ? 'border-[#2447F9] text-[#2447F9] dark:text-blue-300'
  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
</script>

<template>
  <div class="flex items-center gap-1 border-b border-default">
    <button type="button" @click="tab = 'cambios'" class="flex items-center gap-1.5 h-9 px-3 -mb-px border-b-2 text-[12px] font-semibold transition-colors" :class="clase(tab === 'cambios')">
      <History :size="13" /> Registro de cambios
    </button>
    <button
      v-if="renovacionesDisponible"
      type="button"
      @click="tab = 'renovaciones'"
      class="flex items-center gap-1.5 h-9 px-3 -mb-px border-b-2 text-[12px] font-semibold transition-colors"
      :class="clase(tab === 'renovaciones')"
    >
      <RefreshCw :size="13" /> Renovaciones
    </button>
  </div>
</template>
