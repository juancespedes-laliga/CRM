<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, Loader2, AlertCircle, ArrowRight } from 'lucide-vue-next'
import type { ObjetivoHistorial, RegistroCambio } from '../types/auditoria'
import { getHistorial } from '../services/auditoria.api'
import { ACCION_LABEL, CLASE_NEUTRA, MODULO_POR_KEY, ORIGEN_LABEL, claseEstado } from '../constants/auditoria.constants'
import { formatoFechaHora } from '../utils/fechas'
import CamposCambiados from '../components/CamposCambiados.vue'

const props = defineProps<{ objetivo: ObjetivoHistorial | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ detalle: [c: RegistroCambio] }>()

const eventos = ref<RegistroCambio[]>([])
const cargando = ref(false)
const error = ref<string | null>(null)

watch(() => [visible.value, props.objetivo] as const, async ([abierto, obj]) => {
  if (!abierto || !obj) return
  cargando.value = true
  error.value = null
  eventos.value = []
  try {
    eventos.value = await getHistorial(obj.modulo, obj.registroId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo cargar el historial.'
  } finally {
    cargando.value = false
  }
}, { immediate: true })
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[9999]">
    <div class="fixed inset-0 bg-black/30 backdrop-blur-sm" @click="visible = false" />
    <div class="fixed right-0 top-0 h-full w-full max-w-md bg-white dark:bg-slate-800 shadow-2xl flex flex-col z-10" role="dialog" aria-label="Historial">
      <div class="flex items-center justify-between px-5 py-4 border-b border-default surface-header">
        <div class="min-w-0">
          <h3 class="text-[13px] font-bold text-heading">Historial</h3>
          <p v-if="objetivo" class="text-[11px] text-muted truncate">
            {{ objetivo.nombre }} · {{ MODULO_POR_KEY[objetivo.modulo].label }} · ID {{ objetivo.registroId }}<template v-if="objetivo.documento"> · {{ objetivo.documento }}</template>
          </p>
        </div>
        <button @click="visible = false" aria-label="Cerrar" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="flex-1 overflow-y-auto p-5">
        <div v-if="cargando" class="flex items-center justify-center gap-2 text-[11px] text-muted py-8">
          <Loader2 :size="14" class="animate-spin" /> Cargando historial...
        </div>
        <div v-else-if="error" class="flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        </div>
        <p v-else-if="eventos.length === 0" class="text-center text-[11px] text-muted py-8">Este registro no tiene cambios auditados.</p>

        <ol v-else class="relative border-l border-slate-200 dark:border-slate-700 ml-1.5 space-y-5">
          <li v-for="e in eventos" :key="e.id" class="pl-5 relative">
            <span class="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-600 ring-4 ring-white dark:ring-slate-800" />
            <button type="button" @click="emit('detalle', e)" class="w-full text-left rounded-xl -mx-2 px-2 py-1 surface-hover transition-colors">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="px-2 py-0.5 rounded-md text-[10px] font-semibold" :class="CLASE_NEUTRA">{{ ACCION_LABEL[e.accion] }}</span>
                <span class="text-[10px] text-muted tabular-nums">{{ formatoFechaHora(e.fecha) }}</span>
              </div>
              <p class="text-[11px] text-body mt-1">
                {{ e.usuario.nombre }} <span class="text-muted">· {{ ORIGEN_LABEL[e.origen] }}</span>
              </p>
              <p v-if="e.estadoAntes && e.estadoAntes !== e.estadoDespues" class="flex items-center gap-1 text-[11px] font-semibold mt-0.5">
                <span :class="claseEstado(e.estadoAntes)">{{ e.estadoAntes }}</span>
                <ArrowRight :size="10" class="text-slate-400 dark:text-slate-500" />
                <span :class="claseEstado(e.estadoDespues)">{{ e.estadoDespues }}</span>
              </p>
              <p v-if="e.motivo" class="text-[11px] text-subtle mt-0.5 italic">“{{ e.motivo }}”</p>
              <div v-if="e.campos.some(c => c.campo !== 'ESTADO')" class="mt-1.5">
                <CamposCambiados :campos="e.campos.filter(c => c.campo !== 'ESTADO')" compacto />
              </div>
            </button>
          </li>
        </ol>
      </div>
    </div>
  </div>
</template>
