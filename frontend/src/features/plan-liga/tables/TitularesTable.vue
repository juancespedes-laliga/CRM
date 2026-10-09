<script setup lang="ts">
import { Edit2, Loader2, ToggleLeft, ToggleRight, Users, ClipboardList, RefreshCw, CalendarClock } from 'lucide-vue-next'
import type { Titular } from '../types/plan-liga'
import { estadoTitularStyle, planStyle, cupoMaximoTitular } from '../constants/plan-liga.constants'
import PersonaAvatar from '../components/PersonaAvatar.vue'
import CuposIndicador from '../components/CuposIndicador.vue'

defineProps<{
  rows: Titular[]
  activosPorTitular: (id: number) => number
  cargandoEditarId?: number | null
  puedeGestionar: boolean
  puedeDesactivar: boolean
  puedeEditarFecha: boolean
}>()

const emit = defineEmits<{
  seguimiento: [t: Titular]
  editar: [t: Titular]
  'toggle-estado': [t: Titular]
  'editar-fecha': [t: Titular]
  beneficiarios: [t: Titular]
  reemplazar: [t: Titular]
}>()

// El backend trae el conteo real de beneficiarios por plan (planesDetalle); si no viene
// (titulares creados/editados localmente), se usa el conteo mock con el tope fijo.
const cuposTitular = (t: Titular, activosLocal: number) => ({
  activos: t.planesDetalle?.length ? t.planesDetalle.reduce((sum, p) => sum + p.activos, 0) : activosLocal,
  cupo: cupoMaximoTitular(t),
})
</script>

<template>
  <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[1090px] table-fixed">
        <thead class="bg-[#F8FAFC] dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
          <tr>
            <th class="text-left px-4 py-3 w-[200px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Titular</th>
            <th class="text-left px-3 py-3 w-[105px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Documento</th>
            <th class="text-left px-3 py-3 w-[115px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Empresa</th>
            <th class="text-left px-3 py-3 w-[105px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Plan Contratado</th>
            <th class="text-left px-3 py-3 w-[110px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Tipo de Plan</th>
            <th class="text-left px-3 py-3 w-[125px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Beneficiarios</th>
            <th class="text-left px-3 py-3 w-[90px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Inscripción</th>
            <th class="text-left px-3 py-3 w-[75px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Estado</th>
            <th class="text-center px-4 py-3 w-[215px] text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
          <tr v-for="t in rows" :key="t.id" class="hover:bg-slate-50/60 dark:hover:bg-slate-700/40 transition-colors group">
            <td class="px-4 py-3.5 align-top">
              <div class="flex items-start gap-2.5">
                <PersonaAvatar :nombre="t.nombre" class="shrink-0" />
                <div class="min-w-0">
                  <div class="text-[12px] font-semibold text-[#0F172A] dark:text-slate-100 break-words leading-tight">{{ t.nombre }}</div>
                  <div class="text-[10px] text-slate-400 dark:text-slate-500 truncate">{{ t.correo }}</div>
                  <div class="text-[10px] text-slate-400 dark:text-slate-500 truncate">{{ t.telefono }}</div>
                </div>
              </div>
            </td>
            <td class="px-3 py-3.5 align-top text-[11px] text-slate-600 dark:text-slate-300 font-medium break-words">{{ t.documento }}</td>
            <td class="px-3 py-3.5 align-top text-[11px] text-slate-600 dark:text-slate-300 truncate">{{ t.empresa }}</td>
            <td class="px-3 py-3.5 align-top">
              <div v-if="t.planesDetalle?.length" class="flex flex-col gap-0.5">
                <span v-for="(p, i) in t.planesDetalle" :key="p.nombre || i" class="text-[11px] font-semibold" :class="planStyle(p.nombre || 'Estándar')">
                  {{ p.nombre || 'Estándar' }}
                </span>
              </div>
              <span v-else class="text-[11px] font-semibold" :class="planStyle(t.planContratado || 'Estándar')">{{ t.planContratado || 'Estándar' }}</span>
            </td>
            <td class="px-3 py-3.5 align-top text-[11px] text-slate-600 dark:text-slate-300 truncate" :title="t.tipoPlan">{{ t.tipoPlan || '—' }}</td>
            <td class="px-4 py-3.5 align-top overflow-hidden">
              <!-- Número arriba, puntos abajo (en vez de al lado): con planes de cupo alto
                   (6, 8...) el número al lado forzaba a toda la fila a desbordarse sobre la
                   columna de Inscripción, aunque los puntos por sí solos ya envolvieran. -->
              <span class="text-[11px] font-bold block" :class="cuposTitular(t, activosPorTitular(t.id)).activos >= cuposTitular(t, activosPorTitular(t.id)).cupo ? 'text-[#EC4899]' : 'text-slate-600 dark:text-slate-300'">{{ cuposTitular(t, activosPorTitular(t.id)).activos }}/{{ cuposTitular(t, activosPorTitular(t.id)).cupo }}</span>
              <CuposIndicador :activos="cuposTitular(t, activosPorTitular(t.id)).activos" :max="cuposTitular(t, activosPorTitular(t.id)).cupo" variant="dots" class="mt-1" />
              <button @click="emit('beneficiarios', t)" class="text-[13px] leading-tight text-slate-900 font-normal dark:text-white hover:underline mt-1.5 block text-center cursor-pointer">Ver beneficiarios</button>
            </td>
            <td class="px-3 py-3.5 align-top text-[11px] text-slate-500 dark:text-slate-400">{{ t.fechaInscripcion }}</td>
            <td class="px-3 py-3.5 align-top">
              <span class="text-[11px] font-semibold" :class="estadoTitularStyle(t.estado)">{{ t.estado }}</span>
            </td>
            <td class="px-4 py-3.5 align-top text-center whitespace-nowrap">
              <div class="inline-flex items-center justify-center gap-1">
                <button v-if="puedeGestionar" @click="emit('seguimiento', t)"
                  class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#D1FAE5] dark:hover:bg-emerald-950/50 hover:text-[#059669] dark:hover:text-emerald-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all"
                  title="Registrar seguimiento">
                  <ClipboardList :size="12" />
                </button>
                <button v-if="puedeGestionar" @click="emit('editar', t)" :disabled="cargandoEditarId === t.id"
                  class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all disabled:opacity-60"
                  title="Editar">
                  <Loader2 v-if="cargandoEditarId === t.id" :size="12" class="animate-spin" />
                  <Edit2 v-else :size="12" />
                </button>
                <button v-if="puedeEditarFecha" @click="emit('editar-fecha', t)"
                  class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all"
                  title="Editar fecha de inscripción">
                  <CalendarClock :size="12" />
                </button>
                <button v-if="t.estado === 'Activo' ? puedeDesactivar : puedeGestionar" @click="emit('toggle-estado', t)"
                  class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all"
                  :class="t.estado === 'Activo' ? 'hover:bg-red-50 dark:hover:bg-red-950/50 hover:text-red-500 dark:hover:text-red-400' : 'hover:bg-emerald-50 dark:hover:bg-emerald-950/50 hover:text-emerald-600 dark:hover:text-emerald-400'"
                  :title="t.estado === 'Activo' ? 'Desactivar' : 'Activar'">
                  <component :is="t.estado === 'Activo' ? ToggleRight : ToggleLeft" :size="14" />
                </button>
                <button @click="emit('beneficiarios', t)"
                  class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#FCE7F3] dark:hover:bg-pink-950/50 hover:text-[#EC4899] text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all"
                  title="Beneficiarios"><Users :size="12" /></button>
                <button v-if="puedeGestionar && t.estado === 'Activo'" @click="emit('reemplazar', t)"
                  class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-amber-50 dark:hover:bg-amber-950/50 hover:text-amber-600 dark:hover:text-amber-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all"
                  title="Reemplazar"><RefreshCw :size="12" /></button>
              </div>
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="9" class="text-center py-16 text-slate-400 dark:text-slate-500 text-[12px]">No se encontraron titulares.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
