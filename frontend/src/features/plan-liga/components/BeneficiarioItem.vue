<script setup lang="ts">
import { Edit2, ToggleLeft, ToggleRight, RefreshCw, ArrowLeftRight, ClipboardList } from 'lucide-vue-next'
import type { Beneficiario } from '../types/plan-liga'
import { estadoBeneStyle, formatearFechaCorta } from '../constants/plan-liga.constants'
import PersonaAvatar from './PersonaAvatar.vue'

defineProps<{ beneficiario: Beneficiario; puedeGestionar: boolean; puedeDesactivar: boolean }>()
const emit = defineEmits<{
  editar: []
  activar: []
  desactivar: []
  reemplazar: []
  'cambiar-titular': []
  seguimiento: []
}>()
</script>

<template>
  <div
    class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 group hover:shadow-sm transition-all"
    :class="beneficiario.estado === 'Retirado' || beneficiario.estado === 'Reemplazado' ? 'opacity-60' : ''"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="flex items-center gap-3 min-w-0">
        <PersonaAvatar :nombre="beneficiario.nombre" size="sm" bg="#EEF2FF" color="#2447F9" />
        <div class="min-w-0">
          <div class="text-[12px] font-semibold text-[#0F172A] dark:text-slate-100 truncate">{{ beneficiario.nombre }}</div>
          <div class="text-[10px] text-slate-400 dark:text-slate-500">{{ beneficiario.tipoDocumento }} {{ beneficiario.documento }}</div>
          <div class="text-[10px] text-slate-400 dark:text-slate-500">Nac: {{ beneficiario.fechaNacimiento }}<template v-if="beneficiario.sexo"> · {{ beneficiario.sexo }}</template></div>
        </div>
      </div>
      <span class="text-[10px] font-semibold shrink-0" :class="estadoBeneStyle(beneficiario.estado)">{{ beneficiario.estado }}</span>
    </div>
    <div v-if="beneficiario.correo || beneficiario.telefono || beneficiario.direccion || beneficiario.empresa || beneficiario.fechaInscripcion"
      class="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 grid grid-cols-2 gap-x-3 gap-y-1.5">
      <div v-if="beneficiario.correo" class="min-w-0">
        <div class="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Correo</div>
        <div class="text-[11px] text-slate-600 dark:text-slate-300 truncate">{{ beneficiario.correo }}</div>
      </div>
      <div v-if="beneficiario.telefono" class="min-w-0">
        <div class="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Teléfono</div>
        <div class="text-[11px] text-slate-600 dark:text-slate-300 truncate">{{ beneficiario.telefono }}</div>
      </div>
      <div v-if="beneficiario.direccion" class="col-span-2 min-w-0">
        <div class="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Dirección</div>
        <div class="text-[11px] text-slate-600 dark:text-slate-300 truncate">{{ beneficiario.direccion }}</div>
      </div>
      <div v-if="beneficiario.ciudad || beneficiario.departamento" class="min-w-0">
        <div class="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Ciudad / Depto.</div>
        <div class="text-[11px] text-slate-600 dark:text-slate-300 truncate">{{ beneficiario.ciudad }} / {{ beneficiario.departamento }}</div>
      </div>
      <div v-if="beneficiario.empresa" class="min-w-0">
        <div class="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Empresa</div>
        <div class="text-[11px] text-slate-600 dark:text-slate-300 truncate">{{ beneficiario.empresa }}</div>
      </div>
      <div v-if="beneficiario.fechaInscripcion" class="min-w-0">
        <div class="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Inscripción</div>
        <div class="text-[11px] text-slate-600 dark:text-slate-300 truncate">{{ formatearFechaCorta(beneficiario.fechaInscripcion) }}</div>
      </div>
    </div>
    <div class="flex flex-wrap items-center gap-1.5 mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 lg:group-focus-within:opacity-100 transition-opacity">
      <button v-if="puedeGestionar" @click="emit('seguimiento')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#D1FAE5] dark:hover:bg-emerald-950/50 hover:text-[#059669] dark:hover:text-emerald-400 text-slate-500 dark:text-slate-400 text-[12px] font-bold transition-all"><ClipboardList :size="13" /> Seguimiento</button>
      <button v-if="puedeGestionar" @click="emit('editar')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 text-[12px] font-bold transition-all"><Edit2 :size="13" /> Editar</button>
      <button v-if="puedeDesactivar && beneficiario.estado === 'Activo'" @click="emit('desactivar')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-red-50 dark:hover:bg-red-950/50 hover:text-red-500 dark:hover:text-red-400 text-slate-500 dark:text-slate-400 text-[12px] font-bold transition-all"><ToggleLeft :size="13" /> Desactivar</button>
      <button v-else-if="puedeGestionar && beneficiario.estado === 'Inactivo'" @click="emit('activar')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-emerald-50 dark:hover:bg-emerald-950/50 hover:text-emerald-600 dark:hover:text-emerald-400 text-slate-500 dark:text-slate-400 text-[12px] font-bold transition-all"><ToggleRight :size="13" /> Activar</button>
      <button v-if="puedeGestionar && beneficiario.estado === 'Activo'" @click="emit('reemplazar')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-amber-50 dark:hover:bg-amber-950/50 hover:text-amber-600 dark:hover:text-amber-400 text-slate-500 dark:text-slate-400 text-[12px] font-bold transition-all"><RefreshCw :size="13" /> Reemplazar</button>
      <button v-if="puedeGestionar && beneficiario.estado !== 'Retirado' && beneficiario.estado !== 'Reemplazado'" @click="emit('cambiar-titular')" class="flex items-center gap-1.5 h-8 px-3 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 text-[12px] font-bold transition-all"><ArrowLeftRight :size="13" /> Cambiar titular</button>
    </div>
  </div>
</template>
