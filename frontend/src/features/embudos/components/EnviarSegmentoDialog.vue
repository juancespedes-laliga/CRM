<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { X, Mail, MessageCircle, Check, Send, AlertTriangle } from 'lucide-vue-next'
import { PLANTILLAS_CORREO, PLANTILLAS_WHATSAPP, type PlantillaRef } from '../constants/ciclo-afiliado.constants'
import ConfirmDialog from './ConfirmDialog.vue'

const props = defineProps<{ total: number }>()
const visible = defineModel<boolean>('visible', { required: true })

const canal = ref<'correo' | 'whatsapp'>('correo')
const plantillaId = ref('')
const enviando = ref(false)
const resultado = ref('')
const confirmando = ref(false)

const plantillas = computed<PlantillaRef[]>(() => canal.value === 'correo' ? PLANTILLAS_CORREO : PLANTILLAS_WHATSAPP)
const plantillaElegida = computed(() => plantillas.value.find(x => x.id === plantillaId.value))

watch(visible, (v) => {
  if (v) { canal.value = 'correo'; plantillaId.value = ''; resultado.value = ''; enviando.value = false; confirmando.value = false }
})
watch(canal, () => { plantillaId.value = '' })

const puedeEnviar = computed(() => !!plantillaId.value && !enviando.value)

const mensajeConfirmacion = computed(() => {
  const via = canal.value === 'correo' ? 'correo' : 'WhatsApp'
  return `Se va a enviar por ${via} a ${props.total} personas, con la plantilla "${plantillaElegida.value?.nombre}". ¿Continuar?`
})

async function enviar() {
  confirmando.value = false
  enviando.value = true
  await new Promise(r => setTimeout(r, 600))
  const via = canal.value === 'correo' ? 'correos' : 'WhatsApp'
  resultado.value = `Se enviarían ${props.total} ${via} con la plantilla "${plantillaElegida.value?.nombre}". (Demo: no se envía nada.)`
  enviando.value = false
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="surface-card rounded-2xl shadow-2xl w-full max-w-md flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div>
          <h3 class="text-[14px] font-bold text-heading">Enviar al segmento</h3>
          <p class="text-[11px] text-muted mt-0.5"><strong class="text-heading">{{ total }}</strong> personas seleccionadas</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-4">
        <div v-if="resultado" class="rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 px-4 py-3 text-[12px] text-emerald-700 dark:text-emerald-300 flex items-start gap-2">
          <Check :size="15" class="mt-0.5 shrink-0" /><span>{{ resultado }}</span>
        </div>

        <div v-if="!resultado" class="rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-[11px] text-amber-700 dark:text-amber-300 flex items-start gap-2">
          <AlertTriangle :size="14" class="mt-0.5 shrink-0" />
          <span>El envío real de correos y WhatsApp todavía no está conectado a ningún proveedor — esto es solo una vista previa, no se enviará nada de verdad.</span>
        </div>

        <template v-if="!resultado">
          <div>
            <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-2">Canal</label>
            <div class="grid grid-cols-2 gap-2">
              <button
                @click="canal = 'correo'"
                class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-bold transition-all"
                :class="canal === 'correo' ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 font-bold dark:text-white' : 'border-default bg-white dark:bg-slate-800 text-body'"
              ><Mail :size="13" /> Correo</button>
              <button
                @click="canal = 'whatsapp'"
                class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-bold transition-all"
                :class="canal === 'whatsapp' ? 'border-[#059669] bg-[#D1FAE5] dark:bg-emerald-950/40 text-[#059669] dark:text-emerald-300' : 'border-default bg-white dark:bg-slate-800 text-body'"
              ><MessageCircle :size="13" /> WhatsApp</button>
            </div>
          </div>

          <div>
            <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-2">Plantilla de {{ canal === 'correo' ? 'correo' : 'WhatsApp' }}</label>
            <div class="space-y-1.5">
              <button
                v-for="p in plantillas"
                :key="p.id"
                @click="plantillaId = p.id"
                class="w-full text-left px-3 py-2 rounded-lg border transition-all"
                :class="plantillaId === p.id ? 'border-[#2447F9] bg-[#EEF2FF]/60 dark:bg-blue-950/30' : 'border-default hover:bg-slate-50 dark:hover:bg-slate-800'"
              >
                <div class="text-[12px] font-bold text-heading flex items-center gap-1.5">
                  <span v-if="plantillaId === p.id" class="w-3.5 h-3.5 rounded-full bg-[#2447F9] text-white grid place-items-center"><Check :size="9" /></span>
                  {{ p.nombre }}
                </div>
                <div class="text-[10px] text-muted truncate mt-0.5">{{ p.resumen }}</div>
              </button>
            </div>
          </div>
        </template>
      </div>

      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-default surface-header">
        <button @click="visible = false" class="h-9 px-5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
          {{ resultado ? 'Cerrar' : 'Cancelar' }}
        </button>
        <button
          v-if="!resultado"
          @click="confirmando = true"
          :disabled="!puedeEnviar"
          class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50"
        ><Send :size="13" /> {{ enviando ? 'Enviando…' : `Enviar (${total})` }}</button>
      </div>
    </div>

    <ConfirmDialog
      :visible="confirmando"
      titulo="Confirmar envío"
      :mensaje="mensajeConfirmacion"
      texto-confirmar="Enviar"
      :cargando="enviando"
      @confirmar="enviar"
      @cancelar="confirmando = false"
    />
  </div>
</template>
