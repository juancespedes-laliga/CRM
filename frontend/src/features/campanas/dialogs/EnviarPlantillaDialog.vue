<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { X, Send, User, Users, Check, AlertTriangle } from 'lucide-vue-next'
import type { ResultadoEnvioPlantilla } from '../types/plantilla'
import { esCorreoValido, parsearCorreos } from '../constants/campanas.constants'
import { enviarPlantilla } from '../services/plantillas.api'
import { usePlantillas } from '../composables/usePlantillas'

const props = defineProps<{ plantilla: { nombre: string; asunto: string; html: string } | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ enviado: [ResultadoEnvioPlantilla] }>()

const { grupos, guardarComoGrupo } = usePlantillas()

const modo = ref<'persona' | 'grupo'>('persona')
const correoPersona = ref('')
const grupoTexto = ref('')
const grupoSelId = ref('')
const asuntoFinal = ref('')

const nuevoGrupo = ref(false)
const nombreNuevoGrupo = ref('')

const enviando = ref(false)
const error = ref<string | null>(null)
const resultado = ref<ResultadoEnvioPlantilla | null>(null)

watch(visible, (v) => {
  if (!v) return
  modo.value = 'persona'
  correoPersona.value = ''
  grupoTexto.value = ''
  grupoSelId.value = ''
  nuevoGrupo.value = false
  nombreNuevoGrupo.value = ''
  error.value = null
  resultado.value = null
  asuntoFinal.value = props.plantilla?.asunto ?? ''
})

const usarGrupoGuardado = (id: string) => {
  grupoSelId.value = id
  const g = grupos.value.find(x => x.id === id)
  if (g) grupoTexto.value = g.correos.join(', ')
}

const destinatarios = computed<string[]>(() => {
  if (modo.value === 'persona') {
    return esCorreoValido(correoPersona.value) ? [correoPersona.value.trim()] : []
  }
  return parsearCorreos(grupoTexto.value).filter(esCorreoValido)
})
const invalidos = computed<string[]>(() =>
  modo.value === 'grupo'
    ? parsearCorreos(grupoTexto.value).filter(c => !esCorreoValido(c))
    : (correoPersona.value.trim() && !esCorreoValido(correoPersona.value) ? [correoPersona.value.trim()] : []),
)

const puedeEnviar = computed(() =>
  !!props.plantilla && destinatarios.value.length > 0 && !enviando.value,
)

async function enviar() {
  if (!props.plantilla || !puedeEnviar.value) return
  enviando.value = true
  error.value = null
  resultado.value = null
  try {
    const r = await enviarPlantilla({
      plantilla: props.plantilla.nombre,
      asunto: asuntoFinal.value.trim() || props.plantilla.nombre,
      html: props.plantilla.html,
      destinatarios: destinatarios.value,
    })
    if (modo.value === 'grupo' && nuevoGrupo.value && nombreNuevoGrupo.value.trim()) {
      guardarComoGrupo(nombreNuevoGrupo.value, destinatarios.value)
    }
    resultado.value = r
    emit('enviado', r)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo enviar el correo.'
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="surface-card rounded-2xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div>
          <h3 class="text-[14px] font-bold text-heading">Enviar plantilla</h3>
          <p class="text-[11px] text-muted mt-0.5 truncate">{{ plantilla?.nombre || '—' }}</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-4 overflow-y-auto max-h-[70vh]">
        <!-- Éxito -->
        <div v-if="resultado" class="space-y-2">
          <div class="rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 px-4 py-3 text-[12px] text-emerald-700 dark:text-emerald-300 flex items-start gap-2">
            <Check :size="15" class="mt-0.5 shrink-0" />
            <span>
              Correo enviado a <strong>{{ resultado.enviados ?? resultado.destinatarios.length }}</strong> destinatario(s).
              <span v-if="resultado.destinatarios.length" class="block text-[11px] opacity-80 mt-0.5">{{ resultado.destinatarios.join(', ') }}</span>
            </span>
          </div>
          <div v-if="resultado.fallos?.length" class="rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-[11px] text-amber-700 dark:text-amber-300">
            <div class="flex items-center gap-1.5 font-semibold"><AlertTriangle :size="13" /> {{ resultado.fallos.length }} no se pudo(ieron) enviar</div>
            <ul class="mt-1 space-y-0.5">
              <li v-for="f in resultado.fallos" :key="f.correo"><strong>{{ f.correo }}</strong> — {{ f.error }}</li>
            </ul>
          </div>
        </div>

        <template v-if="!resultado">
          <!-- Asunto -->
          <div>
            <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Asunto</label>
            <input v-model="asuntoFinal" placeholder="Asunto del correo" class="w-full h-10 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] transition-all" />
          </div>

          <!-- Persona / Grupo -->
          <div>
            <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Destinatarios</label>
            <div class="flex gap-2">
              <button
                @click="modo = 'persona'"
                class="flex items-center gap-1.5 h-8 px-3 rounded-lg border text-[11px] font-semibold transition-all"
                :class="modo === 'persona' ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 font-bold dark:text-white' : 'border-default bg-white dark:bg-slate-800 text-body'"
              ><User :size="13" /> Una persona</button>
              <button
                @click="modo = 'grupo'"
                class="flex items-center gap-1.5 h-8 px-3 rounded-lg border text-[11px] font-semibold transition-all"
                :class="modo === 'grupo' ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 font-bold dark:text-white' : 'border-default bg-white dark:bg-slate-800 text-body'"
              ><Users :size="13" /> Grupo de correos</button>
            </div>
          </div>

          <div v-if="modo === 'persona'">
            <input v-model="correoPersona" type="email" placeholder="correo@dominio.com" class="w-full h-10 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] transition-all" />
          </div>

          <div v-else class="space-y-2">
            <select
              v-if="grupos.length"
              :value="grupoSelId"
              @change="usarGrupoGuardado(($event.target as HTMLSelectElement).value)"
              class="w-full h-9 px-3 rounded-lg input-surface text-[11px] font-medium outline-none cursor-pointer"
            >
              <option value="">Grupo guardado…</option>
              <option v-for="g in grupos" :key="g.id" :value="g.id">{{ g.nombre }} ({{ g.correos.length }})</option>
            </select>
            <textarea
              v-model="grupoTexto"
              rows="4"
              placeholder="Pega varios correos separados por coma, espacio o salto de línea"
              class="w-full px-3 py-2 rounded-lg input-surface text-[12px] font-mono outline-none focus:border-[#2447F9] transition-all resize-none"
            />
            <label class="flex items-center gap-2 text-[11px] text-body">
              <input type="checkbox" v-model="nuevoGrupo" class="w-3.5 h-3.5 accent-[#2447F9]" />
              Guardar esta lista como grupo
            </label>
            <input
              v-if="nuevoGrupo"
              v-model="nombreNuevoGrupo"
              placeholder="Nombre del grupo (ej. Empresas Pereira)"
              class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] transition-all"
            />
          </div>

          <div class="flex items-center justify-between text-[11px]">
            <span class="text-muted"><strong class="text-heading">{{ destinatarios.length }}</strong> destinatario(s) válidos</span>
            <span v-if="invalidos.length" class="text-amber-600 dark:text-amber-400 flex items-center gap-1">
              <AlertTriangle :size="12" /> {{ invalidos.length }} inválido(s) se omiten
            </span>
          </div>

          <div v-if="error" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">
            {{ error }}
          </div>

          <p class="text-[10px] text-muted">
            Se envía un correo individual a cada destinatario (no se ven entre sí), con la plantilla tal como quedó en el editor.
          </p>
        </template>
      </div>

      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-default surface-header">
        <button @click="visible = false" class="h-9 px-5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
          {{ resultado ? 'Cerrar' : 'Cancelar' }}
        </button>
        <button
          v-if="!resultado"
          @click="enviar"
          :disabled="!puedeEnviar"
          class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50"
        >
          <Send :size="13" /> {{ enviando ? 'Enviando…' : `Enviar (${destinatarios.length})` }}
        </button>
      </div>
    </div>
  </div>
</template>
