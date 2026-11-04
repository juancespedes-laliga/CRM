<script setup lang="ts">
// Envío masivo de WhatsApp por MailerTurbo con una plantilla aprobada por Meta.
// Solo se puede escribir primero a alguien con plantillas aprobadas: no hay texto libre.
import { computed, ref, watch } from 'vue'
import { X, MessageCircle, Check, Send, AlertTriangle, Loader2, Wallet, FlaskConical } from 'lucide-vue-next'
import ConfirmDialog from './ConfirmDialog.vue'
import type { AudienciaCompletaMT, ContactoMT, PlantillaWhatsAppMT, ResultadoEnvioWhatsAppMT, SaldoWhatsAppMT } from '@/features/mailerturbo/types/mailerturbo'
import {
  enviarPruebaWhatsApp, enviarWhatsApp, getPlantillasWhatsApp, getSaldoWhatsApp, normalizarCelular,
} from '@/features/mailerturbo/services/mailerturbo.api'

const props = defineProps<{
  /** Personas seleccionadas (se descartan las que no tienen celular válido). */
  contactos: ContactoMT[]
  /** "Seleccionar toda la audiencia": el backend arma la lista con los filtros. */
  audiencia?: AudienciaCompletaMT
}>()
const visible = defineModel<boolean>('visible', { required: true })

const plantillas = ref<PlantillaWhatsAppMT[]>([])
const saldo = ref<SaldoWhatsAppMT | null>(null)
const cargando = ref(false)
const errorCarga = ref('')
const plantillaNombre = ref('')
const enviando = ref(false)
const confirmando = ref(false)
const resultado = ref<ResultadoEnvioWhatsAppMT | null>(null)
const errorEnvio = ref('')

const telefonoPrueba = ref('')
const probando = ref(false)
const mensajePrueba = ref<{ ok: boolean; texto: string } | null>(null)

// Celulares únicos válidos entre los seleccionados (con toda la audiencia lo calcula el backend).
const conCelular = computed(() => new Set(props.contactos.map(c => normalizarCelular(c.telefono)).filter(Boolean)).size)
const totalTexto = computed(() =>
  props.audiencia ? `${props.audiencia.total} personas (se descartan las que no tengan celular)` : `${conCelular.value} con celular válido`,
)
const plantillaElegida = computed(() => plantillas.value.find(p => p.nombre === plantillaNombre.value))
const sinSaldo = computed(() => saldo.value !== null && saldo.value.saldo <= 0)
const hayDestinatarios = computed(() => (props.audiencia ? props.audiencia.total > 0 : conCelular.value > 0))
const puedeEnviar = computed(() => !!plantillaElegida.value && hayDestinatarios.value && !enviando.value)

async function cargar() {
  cargando.value = true
  errorCarga.value = ''
  try {
    const [p, s] = await Promise.all([getPlantillasWhatsApp(), getSaldoWhatsApp().catch(() => null)])
    plantillas.value = p
    saldo.value = s
  } catch (e) {
    errorCarga.value = e instanceof Error ? e.message : 'No se pudo consultar MailerTurbo.'
  } finally {
    cargando.value = false
  }
}

watch(visible, (v) => {
  if (!v) return
  plantillaNombre.value = ''
  resultado.value = null
  errorEnvio.value = ''
  mensajePrueba.value = null
  enviando.value = false
  confirmando.value = false
  cargar()
})

const mensajeConfirmacion = computed(() => {
  const n = props.audiencia ? props.audiencia.total : conCelular.value
  return `Se enviará el WhatsApp "${plantillaElegida.value?.nombre}" a ${n} personas. Cada mensaje se cobra del saldo de WhatsApp en MailerTurbo. ¿Continuar?`
})

async function probar() {
  if (!plantillaElegida.value) return
  probando.value = true
  mensajePrueba.value = null
  try {
    await enviarPruebaWhatsApp({ plantilla: plantillaElegida.value.nombre, telefono: telefonoPrueba.value })
    mensajePrueba.value = { ok: true, texto: 'Enviado. Revisa ese WhatsApp.' }
  } catch (e) {
    mensajePrueba.value = { ok: false, texto: e instanceof Error ? e.message : 'No se pudo enviar la prueba.' }
  } finally {
    probando.value = false
  }
}

async function enviar() {
  if (!plantillaElegida.value) return
  confirmando.value = false
  enviando.value = true
  errorEnvio.value = ''
  try {
    resultado.value = await enviarWhatsApp({
      plantilla: plantillaElegida.value.nombre,
      ...(props.audiencia ? { audiencia: props.audiencia.filtros } : { contactos: props.contactos }),
    })
  } catch (e) {
    errorEnvio.value = e instanceof Error ? e.message : 'No se pudo enviar.'
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="surface-card rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div>
          <h3 class="text-[14px] font-bold text-heading flex items-center gap-1.5"><MessageCircle :size="15" class="text-[#059669]" /> Enviar WhatsApp</h3>
          <p class="text-[11px] text-muted mt-0.5">{{ totalTexto }}</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-4 overflow-y-auto">
        <!-- Resultado del envío -->
        <template v-if="resultado">
          <div class="rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 px-4 py-3 text-[12px] text-emerald-700 dark:text-emerald-300 flex items-start gap-2">
            <Check :size="15" class="mt-0.5 shrink-0" />
            <span>
              MailerTurbo aceptó <strong>{{ resultado.enviados }}</strong> de {{ resultado.total }} mensajes.
              <template v-if="resultado.descartados"> {{ resultado.descartados }} personas no tenían celular válido o estaban repetidas.</template>
            </span>
          </div>
          <div v-if="resultado.fallidos" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[11px] text-red-700 dark:text-red-300">
            <p class="font-bold mb-1">{{ resultado.fallidos }} no se pudieron enviar:</p>
            <ul class="space-y-0.5 max-h-40 overflow-y-auto">
              <li v-for="f in resultado.fallos" :key="f.telefono">{{ f.nombre || f.telefono }} ({{ f.telefono }}): {{ f.error }}</li>
            </ul>
          </div>
          <p class="text-[10px] text-muted">El estado (entregado / leído) se ve en MailerTurbo, en los mensajes de WhatsApp.</p>
        </template>

        <template v-else>
          <div v-if="cargando" class="flex items-center gap-2 text-[12px] text-muted py-6 justify-center">
            <Loader2 :size="14" class="animate-spin" /> Consultando MailerTurbo…
          </div>

          <div v-else-if="errorCarga" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[11px] text-red-700 dark:text-red-300 flex items-start gap-2">
            <AlertTriangle :size="14" class="mt-0.5 shrink-0" /><span>{{ errorCarga }}</span>
          </div>

          <template v-else>
            <div v-if="saldo" class="flex items-center justify-between rounded-lg border border-default px-3 py-2 text-[11px]">
              <span class="flex items-center gap-1.5 text-muted"><Wallet :size="13" /> Saldo WhatsApp</span>
              <strong :class="sinSaldo ? 'text-red-600 dark:text-red-400' : 'text-heading'">{{ saldo.saldo.toFixed(2) }} {{ saldo.moneda }}</strong>
            </div>
            <div v-if="sinSaldo" class="rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-[11px] text-amber-700 dark:text-amber-300 flex items-start gap-2">
              <AlertTriangle :size="14" class="mt-0.5 shrink-0" />
              <span>No hay saldo de WhatsApp en MailerTurbo: los mensajes pueden ser rechazados. Recarga la billetera antes de enviar.</span>
            </div>

            <div v-if="!plantillas.length" class="rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-[11px] text-amber-700 dark:text-amber-300 flex items-start gap-2">
              <AlertTriangle :size="14" class="mt-0.5 shrink-0" />
              <span>No hay plantillas de WhatsApp aprobadas en MailerTurbo. Créalas en MailerTurbo y espera la aprobación de Meta; luego aparecerán aquí.</span>
            </div>

            <div v-else>
              <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-2">Plantilla aprobada</label>
              <div class="space-y-1.5">
                <button
                  v-for="p in plantillas"
                  :key="p.nombre"
                  @click="plantillaNombre = p.nombre; mensajePrueba = null"
                  class="w-full text-left px-3 py-2 rounded-lg border transition-all"
                  :class="plantillaNombre === p.nombre ? 'border-[#059669] bg-[#D1FAE5]/60 dark:bg-emerald-950/30' : 'border-default hover:bg-slate-50 dark:hover:bg-slate-800'"
                >
                  <div class="text-[12px] font-bold text-heading flex items-center gap-1.5">
                    <span v-if="plantillaNombre === p.nombre" class="w-3.5 h-3.5 rounded-full bg-[#059669] text-white grid place-items-center"><Check :size="9" /></span>
                    {{ p.nombre }}
                    <span v-if="p.categoria" class="ml-auto text-[9px] font-semibold uppercase text-muted">{{ p.categoria }}</span>
                  </div>
                  <div v-if="p.texto" class="text-[10px] text-muted line-clamp-2 mt-0.5">{{ p.texto }}</div>
                </button>
              </div>
            </div>

            <div v-if="plantillaElegida" class="rounded-lg border border-dashed border-default p-3">
              <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-1.5">Probar primero con un número</label>
              <div class="flex gap-2">
                <input
                  v-model="telefonoPrueba"
                  inputmode="tel"
                  placeholder="300 123 4567"
                  class="flex-1 min-w-0 h-8 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[12px] text-heading"
                />
                <button
                  @click="probar"
                  :disabled="probando || !normalizarCelular(telefonoPrueba)"
                  class="flex items-center gap-1.5 h-8 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
                ><Loader2 v-if="probando" :size="12" class="animate-spin" /><FlaskConical v-else :size="12" /> Probar</button>
              </div>
              <p v-if="mensajePrueba" class="text-[10px] mt-1.5" :class="mensajePrueba.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">{{ mensajePrueba.texto }}</p>
            </div>

            <div v-if="errorEnvio" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[11px] text-red-700 dark:text-red-300 flex items-start gap-2">
              <AlertTriangle :size="14" class="mt-0.5 shrink-0" /><span>{{ errorEnvio }}</span>
            </div>
          </template>
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
          class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#059669] text-white text-[11px] font-bold shadow hover:bg-[#047857] transition-all disabled:opacity-50"
        >
          <Loader2 v-if="enviando" :size="13" class="animate-spin" /><Send v-else :size="13" />
          {{ enviando ? 'Enviando…' : 'Enviar WhatsApp' }}
        </button>
      </div>
    </div>

    <ConfirmDialog
      :visible="confirmando"
      titulo="Confirmar envío de WhatsApp"
      :mensaje="mensajeConfirmacion"
      texto-confirmar="Enviar"
      :cargando="enviando"
      @confirmar="enviar"
      @cancelar="confirmando = false"
    />
  </div>
</template>
