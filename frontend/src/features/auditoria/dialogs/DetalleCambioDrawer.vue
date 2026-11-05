<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, Loader2, AlertCircle, History, ArrowRight } from 'lucide-vue-next'
import type { RegistroCambio } from '../types/auditoria'
import { getCambio } from '../services/auditoria.api'
import {
  ACCION_LABEL, CLASE_NEUTRA, MODULO_POR_KEY, ORIGEN_LABEL, claseEstado, claseRenovado, claseVigencia,
} from '../constants/auditoria.constants'
import { formatoFecha, formatoFechaHora, textoDiasRestantes, vigenciaDe } from '../utils/fechas'
import CamposCambiados from '../components/CamposCambiados.vue'

const props = defineProps<{ cambioId: number | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ historial: [c: RegistroCambio] }>()

const cambio = ref<RegistroCambio | null>(null)
const cargando = ref(false)
const error = ref<string | null>(null)

watch(() => [visible.value, props.cambioId] as const, async ([abierto, id]) => {
  if (!abierto || id === null) return
  cargando.value = true
  error.value = null
  cambio.value = null
  try {
    cambio.value = await getCambio(id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo cargar el detalle del cambio.'
  } finally {
    cargando.value = false
  }
}, { immediate: true })

const dt = 'text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider'
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[9999]" @keydown.esc="visible = false">
    <div class="fixed inset-0 bg-black/30 backdrop-blur-sm" @click="visible = false" />
    <div class="fixed right-0 top-0 h-full w-full max-w-md bg-white dark:bg-slate-800 shadow-2xl flex flex-col z-10" role="dialog" aria-label="Detalle del cambio">
      <div class="flex items-center justify-between px-5 py-4 border-b border-default surface-header">
        <div class="min-w-0">
          <h3 class="text-[13px] font-bold text-heading">Detalle del cambio</h3>
          <p v-if="cambio" class="text-[11px] text-muted truncate">#{{ cambio.id }} · {{ formatoFechaHora(cambio.fecha) }}</p>
        </div>
        <button @click="visible = false" aria-label="Cerrar" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="flex-1 overflow-y-auto p-5 space-y-5">
        <div v-if="cargando" class="flex items-center justify-center gap-2 text-[11px] text-muted py-8">
          <Loader2 :size="14" class="animate-spin" /> Cargando detalle...
        </div>
        <div v-else-if="error" class="flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        </div>

        <template v-else-if="cambio">
          <!-- Acción y registro -->
          <section>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2 py-0.5 rounded-md text-[11px] font-semibold" :class="CLASE_NEUTRA">{{ ACCION_LABEL[cambio.accion] }}</span>
              <span class="text-[11px] text-muted">{{ ORIGEN_LABEL[cambio.origen] }}<template v-if="cambio.loteId"> · lote {{ cambio.loteId }}</template></span>
            </div>
            <p class="mt-2 text-[14px] font-bold text-heading">{{ cambio.registroNombre }}</p>
            <p class="text-[11px] text-muted">{{ MODULO_POR_KEY[cambio.modulo].label }} · ID {{ cambio.registroId }}<template v-if="cambio.documento"> · {{ cambio.documento }}</template></p>
            <p v-if="cambio.grupoTitular" class="text-[11px] text-subtle mt-0.5">Grupo de {{ cambio.grupoTitular.nombre }} ({{ cambio.grupoTitular.documento }})</p>
            <p v-if="cambio.estadoAntes !== cambio.estadoDespues" class="flex items-center gap-1.5 text-[12px] font-semibold mt-2">
              <span :class="claseEstado(cambio.estadoAntes)">{{ cambio.estadoAntes ?? 'Nuevo' }}</span>
              <ArrowRight :size="12" class="text-slate-400 dark:text-slate-500" />
              <span :class="claseEstado(cambio.estadoDespues)">{{ cambio.estadoDespues }}</span>
            </p>
          </section>

          <!-- Quién -->
          <section>
            <h4 :class="dt" class="mb-1.5">Quién lo hizo</h4>
            <dl class="surface-sunken rounded-xl px-3 py-2 grid grid-cols-[80px_1fr] gap-y-1 text-[11px]">
              <dt class="text-subtle font-semibold">Nombre</dt><dd class="text-body">{{ cambio.usuario.nombre }}</dd>
              <dt class="text-subtle font-semibold">Usuario</dt><dd class="text-body">{{ cambio.usuario.usuario }} · ID {{ cambio.usuario.id }}</dd>
              <dt class="text-subtle font-semibold">Rol</dt><dd class="text-body">{{ cambio.usuario.rol || '—' }}</dd>
              <dt class="text-subtle font-semibold">IP</dt><dd class="text-body tabular-nums">{{ cambio.ip }}</dd>
            </dl>
          </section>

          <!-- Motivo -->
          <section>
            <h4 :class="dt" class="mb-1.5">Motivo</h4>
            <p class="text-[12px] text-body">{{ cambio.motivo || 'Sin motivo registrado.' }}</p>
          </section>

          <!-- Vigencia (Plan Liga) -->
          <section v-if="cambio.vigenciaHasta || cambio.renovado !== null">
            <h4 :class="dt" class="mb-1.5">Vigencia en ese momento</h4>
            <dl class="surface-sunken rounded-xl px-3 py-2 grid grid-cols-[80px_1fr] gap-y-1 text-[11px]">
              <dt class="text-subtle font-semibold">Ingreso</dt><dd class="text-body">{{ formatoFecha(cambio.fechaIngreso) }}</dd>
              <dt class="text-subtle font-semibold">Renovado</dt>
              <dd class="font-semibold" :class="claseRenovado(cambio.renovado)">{{ cambio.renovado ? `Sí, ${formatoFecha(cambio.fechaRenovado)}` : 'No' }}</dd>
              <template v-if="cambio.vigenciaHasta">
                <dt class="text-subtle font-semibold">Vence</dt>
                <dd class="text-body">
                  {{ formatoFecha(cambio.vigenciaHasta) }}
                  <span class="font-semibold" :class="claseVigencia(vigenciaDe(cambio.vigenciaHasta))"> · {{ textoDiasRestantes(cambio.vigenciaHasta) }}</span>
                </dd>
              </template>
            </dl>
          </section>

          <!-- Campos -->
          <section>
            <h4 :class="dt" class="mb-1.5">Campos modificados</h4>
            <CamposCambiados :campos="cambio.campos" />
          </section>
        </template>
      </div>

      <div v-if="cambio" class="px-5 py-3 border-t border-default">
        <button type="button" @click="emit('historial', cambio)" class="w-full flex items-center justify-center gap-1.5 h-9 rounded-lg border border-default surface-card text-[11px] font-semibold text-body surface-hover transition-all">
          <History :size="13" /> Ver historial de este registro
        </button>
      </div>
    </div>
  </div>
</template>
