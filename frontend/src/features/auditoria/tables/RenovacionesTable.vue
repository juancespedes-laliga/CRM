<script setup lang="ts">
import { History } from 'lucide-vue-next'
import type { RenovacionRegistro } from '../types/auditoria'
import { VIGENCIA_LABEL, claseEstado, claseRenovado, claseVigencia } from '../constants/auditoria.constants'
import { formatoFecha, textoDiasRestantes, vigenciaDe } from '../utils/fechas'

defineProps<{ rows: RenovacionRegistro[]; cargando: boolean; muestraTipo: boolean }>()
const emit = defineEmits<{ historial: [r: RenovacionRegistro] }>()

const th = 'text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider'
</script>

<template>
  <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
    <!-- Sin ancho mínimo ni scroll horizontal: las celdas se acomodan en varias líneas. -->
    <div class="overflow-x-hidden">
      <table class="w-full">
        <thead class="surface-header border-b border-default">
          <tr>
            <th :class="th" class="pl-5">Persona</th>
            <th :class="th">Empresa / Plan</th>
            <th :class="th">Estado</th>
            <th :class="th">Ingreso</th>
            <th :class="th">Renovado</th>
            <th :class="th">Vencimiento</th>
            <th :class="th">Última renovación por</th>
            <th :class="th" class="text-right pr-5"><span class="sr-only">Historial</span></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
          <tr v-for="r in rows" :key="`${r.tipo}-${r.id}`" class="surface-hover transition-colors group">
            <td class="pl-5 pr-4 py-3 align-top">
              <p class="text-[12px] font-semibold text-heading leading-tight">{{ r.nombre }}</p>
              <p class="text-[10px] text-muted mt-0.5">
                <template v-if="muestraTipo">{{ r.tipo === 'titular' ? 'Titular' : 'Beneficiario' }} · </template>{{ r.documento }}
              </p>
              <p v-if="r.titular" class="text-[10px] text-subtle mt-0.5 truncate max-w-[220px]">Grupo de {{ r.titular.nombre }}</p>
            </td>
            <td class="px-4 py-3 align-top">
              <p class="text-[11px] text-body">{{ r.empresa || '—' }}</p>
              <p class="text-[10px] text-muted mt-0.5">{{ r.plan || '—' }}</p>
            </td>
            <td class="px-4 py-3 align-top">
              <span class="text-[11px] font-semibold" :class="claseEstado(r.estado)">{{ r.estado }}</span>
            </td>
            <td class="px-4 py-3 align-top text-[11px] text-body whitespace-nowrap tabular-nums">{{ formatoFecha(r.fechaIngreso) }}</td>
            <td class="px-4 py-3 align-top whitespace-nowrap">
              <p class="text-[11px] font-semibold" :class="claseRenovado(r.renovado)">{{ r.renovado ? 'Sí' : 'No' }}</p>
              <p v-if="r.fechaRenovado" class="text-[10px] text-muted mt-0.5 tabular-nums">{{ formatoFecha(r.fechaRenovado) }}</p>
            </td>
            <td class="px-4 py-3 align-top whitespace-nowrap">
              <p class="text-[11px] text-body tabular-nums">{{ formatoFecha(r.vencimiento) }}</p>
              <p class="text-[10px] font-semibold mt-0.5" :class="claseVigencia(vigenciaDe(r.vencimiento))" :title="VIGENCIA_LABEL[vigenciaDe(r.vencimiento)]">
                {{ textoDiasRestantes(r.vencimiento) }}
              </p>
            </td>
            <td class="px-4 py-3 align-top">
              <template v-if="r.ultimaRenovacionPor">
                <p class="text-[11px] text-body">{{ r.ultimaRenovacionPor.nombre }}</p>
                <p class="text-[10px] text-muted mt-0.5">{{ r.ultimaRenovacionPor.usuario }}</p>
              </template>
              <span v-else class="text-[11px] text-muted">—</span>
            </td>
            <td class="pr-5 pl-2 py-3 align-top text-right">
              <button
                type="button"
                @click="emit('historial', r)"
                class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 inline-flex items-center justify-center transition-all opacity-60 group-hover:opacity-100"
                title="Historial de la persona"
                aria-label="Historial de la persona"
              >
                <History :size="12" />
              </button>
            </td>
          </tr>
          <tr v-if="!cargando && rows.length === 0">
            <td colspan="8" class="text-center py-16 text-muted text-[12px]">No hay personas que coincidan con los filtros.</td>
          </tr>
          <tr v-if="cargando && rows.length === 0">
            <td colspan="8" class="text-center py-16 text-muted text-[12px]">Cargando renovaciones...</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
