<script setup lang="ts">
import { MapPin, Users, Edit2, Clock, Trash2 } from 'lucide-vue-next'
import type { Empresa } from '../types/empresa'
import { estadoStyle, estadoLabel } from '../constants/empresas.constants'
import EmpresaAvatar from '../components/EmpresaAvatar.vue'

defineProps<{ rows: Empresa[]; puedeGestionar: boolean; puedeEliminar: boolean }>()
const emit = defineEmits<{ editar: [e: Empresa]; historial: [e: Empresa]; borrar: [e: Empresa] }>()
</script>

<template>
  <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[820px]">
        <thead class="bg-[#F8FAFC] dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
          <tr>
            <th class="text-left px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Empresa</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">NIT</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Industria</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Ciudad</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Contactos</th>
            <th class="text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Estado</th>
            <th class="text-right px-5 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
          <tr v-for="e in rows" :key="e.id" class="hover:bg-slate-50/60 dark:hover:bg-slate-700/40 transition-colors group">
            <td class="px-5 py-3.5">
              <div class="flex items-center gap-3">
                <EmpresaAvatar :nombre="e.razonSocial" />
                <div>
                  <div class="text-[12px] font-semibold text-[#0F172A] dark:text-slate-100">{{ e.razonSocial }}</div>
                  <div class="text-[10px] text-slate-400 dark:text-slate-500 flex items-center gap-1"><MapPin :size="9" /> {{ e.direccion }}</div>
                </div>
              </div>
            </td>
            <td class="px-4 py-3.5 text-[11px] text-slate-600 dark:text-slate-300 font-medium">{{ e.nit }}</td>
            <td class="px-4 py-3.5">
              <span class="text-[11px] font-bold text-slate-900 dark:text-white">{{ e.industria }}</span>
            </td>
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-1 text-[11px] text-slate-600 dark:text-slate-300"><MapPin :size="11" class="text-slate-400 dark:text-slate-500" />{{ e.ciudad }}</div>
            </td>
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-1 text-[11px] text-slate-600 dark:text-slate-300"><Users :size="11" class="text-slate-400 dark:text-slate-500" />{{ e.contactos }}</div>
            </td>
            <td class="px-4 py-3.5">
              <span class="text-[11px] font-semibold" :class="estadoStyle(e.estado)">{{ estadoLabel(e.estado) }}</span>
            </td>
            <td class="px-5 py-3.5 text-right">
              <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button v-if="puedeGestionar" @click="emit('editar', e)" class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all" title="Editar">
                  <Edit2 :size="12" />
                </button>
                <button @click="emit('historial', e)" class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-amber-50 dark:hover:bg-amber-950/50 hover:text-amber-600 dark:hover:text-amber-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all" title="Historial">
                  <Clock :size="12" />
                </button>
                <button v-if="puedeEliminar" @click="emit('borrar', e)" class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-red-50 dark:hover:bg-red-950/50 hover:text-red-600 dark:hover:text-red-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all" title="Eliminar">
                  <Trash2 :size="12" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="7" class="text-center py-16 text-slate-400 dark:text-slate-500 text-[12px]">No se encontraron empresas.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
