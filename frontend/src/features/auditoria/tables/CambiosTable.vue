<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight, History, Layers } from 'lucide-vue-next'
import type { RegistroCambio } from '../types/auditoria'
import {
  ACCION_LABEL, CLASE_NEUTRA, MODULO_POR_KEY, ORIGEN_LABEL, claseEstado, claseRenovado, esOrigenMasivo,
} from '../constants/auditoria.constants'
import { formatoFecha, formatoHora } from '../utils/fechas'

const props = defineProps<{
  rows: RegistroCambio[]
  cargando: boolean
  /** Mostrar la columna Módulo (solo cuando se revisan todos los módulos). */
  muestraModulo: boolean
  /** Mostrar ingreso / renovación (Plan Liga). */
  muestraPlanLiga: boolean
}>()
const emit = defineEmits<{ detalle: [c: RegistroCambio]; historial: [c: RegistroCambio] }>()

const esPlanLiga = (c: RegistroCambio) => c.modulo === 'titulares' || c.modulo === 'beneficiarios'
// ID que se muestra: en beneficiarios también el del titular de su grupo.
const idsRegistro = (c: RegistroCambio) =>
  c.modulo === 'beneficiarios' && c.idTitular ? `ID ${c.registroId} · Titular ${c.idTitular}` : `ID ${c.registroId}`

const columnas = computed(() => 5 + (props.muestraPlanLiga ? 1 : 0))
const th = 'text-left px-4 py-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider'
</script>

<template>
  <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
    <!-- Sin ancho mínimo ni scroll horizontal: las celdas se acomodan en varias líneas. -->
    <div class="overflow-x-hidden">
      <table class="w-full">
        <thead class="surface-header border-b border-default">
          <tr>
            <th :class="th" class="pl-5">Fecha</th>
            <th :class="th">Usuario</th>
            <th :class="th">Acción</th>
            <th :class="th">Registro afectado</th>
            <th :class="th">Estado</th>
            <th v-if="muestraPlanLiga" :class="th">Vigencia (ingreso → fin)</th>
            <th :class="th" class="text-right pr-5"><span class="sr-only">Historial</span></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
          <tr
            v-for="c in rows"
            :key="c.id"
            @click="emit('detalle', c)"
            class="surface-hover transition-colors cursor-pointer group"
          >
            <td class="pl-5 pr-4 py-3 align-top">
              <p class="text-[11px] font-semibold text-heading tabular-nums whitespace-nowrap">{{ formatoFecha(c.fecha) }}</p>
              <p class="text-[10px] text-muted tabular-nums mt-0.5">{{ formatoHora(c.fecha) }}</p>
            </td>
            <td class="px-4 py-3 align-top">
              <p class="text-[12px] font-semibold text-heading leading-tight">{{ c.usuario.nombre }}</p>
              <p class="text-[10px] text-muted mt-0.5">{{ c.usuario.usuario }} · ID {{ c.usuario.id }}</p>
            </td>
            <td class="px-4 py-3 align-top">
              <span class="inline-block px-2 py-0.5 rounded-md text-[10px] font-semibold" :class="CLASE_NEUTRA">{{ ACCION_LABEL[c.accion] }}</span>
              <p class="flex items-center gap-1 text-[10px] text-muted mt-1">
                <Layers v-if="esOrigenMasivo(c.origen)" :size="10" />
                {{ ORIGEN_LABEL[c.origen] }}
              </p>
            </td>
            <td class="px-4 py-3 align-top break-words">
              <p class="text-[12px] font-semibold text-heading leading-tight">{{ c.registroNombre }}</p>
              <p class="text-[10px] text-muted mt-0.5">
                <template v-if="muestraModulo">{{ MODULO_POR_KEY[c.modulo].label }} · </template>{{ idsRegistro(c) }}<template v-if="c.documento"> · {{ c.documento }}</template>
              </p>
              <p v-if="c.grupoTitular" class="text-[10px] text-subtle mt-0.5 truncate max-w-[240px]" :title="`Grupo de ${c.grupoTitular.nombre}`">
                Grupo de {{ c.grupoTitular.nombre }}
              </p>
            </td>
            <td class="px-4 py-3 align-top whitespace-nowrap">
              <span v-if="c.estadoAntes && c.estadoAntes !== c.estadoDespues" class="flex items-center gap-1 text-[11px] font-semibold">
                <span :class="claseEstado(c.estadoAntes)">{{ c.estadoAntes }}</span>
                <ArrowRight :size="11" class="text-slate-400 dark:text-slate-500" />
                <span :class="claseEstado(c.estadoDespues)">{{ c.estadoDespues }}</span>
              </span>
              <span v-else-if="c.estadoDespues" class="text-[11px] font-semibold" :class="claseEstado(c.estadoDespues)">{{ c.estadoDespues }}</span>
              <span v-else class="text-[11px] text-muted">—</span>
            </td>
            <td v-if="muestraPlanLiga" class="px-4 py-3 align-top">
              <template v-if="esPlanLiga(c) && (c.fechaIngreso || c.renovado !== null)">
                <p class="text-[11px] text-body tabular-nums">
                  <span class="whitespace-nowrap">{{ formatoFecha(c.fechaIngreso) }}</span>
                  <ArrowRight :size="10" class="inline text-slate-400 dark:text-slate-500 mx-0.5" />
                  <span class="whitespace-nowrap">{{ formatoFecha(c.vigenciaHasta) }}</span>
                </p>
                <p class="text-[10px] mt-0.5 flex flex-wrap items-center gap-x-1.5">
                  <span class="font-semibold whitespace-nowrap" :class="claseRenovado(c.renovado)">{{ c.renovado ? 'Renovado' : 'No renovado' }}</span>
                  <span v-if="c.fechaInscripcion" class="text-muted whitespace-nowrap">· Inscrito {{ formatoFecha(c.fechaInscripcion) }}</span>
                </p>
              </template>
              <span v-else class="text-[11px] text-muted">—</span>
            </td>
            <td class="pr-5 pl-2 py-3 align-top text-right">
              <button
                type="button"
                @click.stop="emit('historial', c)"
                class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-[#EEF2FF] dark:hover:bg-blue-950/50 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 inline-flex items-center justify-center transition-all opacity-60 group-hover:opacity-100"
                title="Historial del registro"
                aria-label="Historial del registro"
              >
                <History :size="12" />
              </button>
            </td>
          </tr>
          <tr v-if="!cargando && rows.length === 0">
            <td :colspan="columnas + 1" class="text-center py-16 text-muted text-[12px]">No hay cambios que coincidan con los filtros.</td>
          </tr>
          <tr v-if="cargando && rows.length === 0">
            <td :colspan="columnas + 1" class="text-center py-16 text-muted text-[12px]">Cargando cambios...</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
