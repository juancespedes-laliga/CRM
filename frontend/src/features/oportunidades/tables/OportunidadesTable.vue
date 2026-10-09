<script setup lang="ts">
import { Building2, User, Award, Layers, DollarSign, Edit2, Trophy, XCircle } from 'lucide-vue-next'
import type { Oportunidad } from '../types/oportunidad'
import { estadoStyle } from '../constants/oportunidades.constants'

defineProps<{ rows: Oportunidad[]; puedeGestionar: boolean }>()
const emit = defineEmits<{
  editar: [o: Oportunidad]
  ganar: [o: Oportunidad]
  perder: [o: Oportunidad]
}>()

const iconoCliente = (o: Oportunidad) => o.tipoCliente === 'titular' ? Award : o.tipoCliente === 'contacto' ? User : Building2

const clientePrincipal = (o: Oportunidad) => {
  if (o.tipoCliente === 'titular') return o.titularNombre || 'Sin titular asociado'
  if (o.tipoCliente === 'contacto') return o.contactoNombre || 'Sin contacto asociado'
  return o.empresaNombre || 'Sin empresa asociada'
}

const clienteSecundario = (o: Oportunidad) => {
  if (o.tipoCliente === 'titular') return 'Titular Plan Liga'
  if (o.tipoCliente === 'contacto') return 'Contacto'
  return o.contactoNombre || 'Sin contacto asociado'
}
</script>

<template>
  <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[1000px]">
        <thead class="surface-header border-b border-default">
          <tr>
            <th class="text-left px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Empresa · Contacto</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Servicio</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Valor</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Etapa</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Responsable</th>
            <th class="text-right px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
          <tr v-for="o in rows" :key="o.id" class="surface-hover transition-colors group">
            <td class="px-5 py-3.5">
              <div class="text-[12px] font-semibold text-heading flex items-center gap-1.5">
                <component :is="iconoCliente(o)" :size="12" class="text-slate-400 dark:text-slate-500" />{{ clientePrincipal(o) }}
              </div>
              <div class="text-[11px] text-muted flex items-center gap-1 mt-0.5"><User :size="10" />{{ clienteSecundario(o) }}</div>
            </td>
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-1 text-[11px] text-body"><Layers :size="11" class="text-slate-400 dark:text-slate-500" />{{ o.servicio }}</div>
            </td>
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-1 text-[13px] font-bold text-heading"><DollarSign :size="12" class="text-slate-400 dark:text-slate-500" />{{ o.valor }}</div>
            </td>
            <td class="px-4 py-3.5">
              <span class="text-[11px] font-semibold" :class="estadoStyle(o.estado)">{{ o.estado }}</span>
            </td>
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-1.5">
                <div class="w-6 h-6 rounded-full bg-[#EEF2FF] dark:bg-blue-950/50 text-slate-900 dark:text-white text-[8px] font-bold flex items-center justify-center flex-shrink-0">
                  {{ o.responsable.split(' ').map(n => n[0]).join('') }}
                </div>
                <span class="text-[11px] text-body truncate max-w-[90px]">{{ o.responsable }}</span>
              </div>
            </td>
            <td class="px-5 py-3.5 text-right">
              <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button v-if="puedeGestionar" @click="emit('editar', o)" class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all" title="Editar"><Edit2 :size="12" /></button>
                <button v-if="puedeGestionar && !['Ganada','Perdida'].includes(o.estado)" @click="emit('ganar', o)" class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-emerald-50 dark:hover:bg-emerald-950/50 hover:text-emerald-600 dark:hover:text-emerald-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all" title="Marcar ganada"><Trophy :size="12" /></button>
                <button v-if="puedeGestionar && !['Ganada','Perdida'].includes(o.estado)" @click="emit('perder', o)" class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-red-50 dark:hover:bg-red-950/50 hover:text-red-500 dark:hover:text-red-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all" title="Marcar perdida"><XCircle :size="12" /></button>
              </div>
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="7" class="text-center py-16 text-muted text-[12px]">No se encontraron oportunidades.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
