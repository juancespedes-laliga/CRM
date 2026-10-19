<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { X, CloudUpload, Check, AlertTriangle, Loader2 } from 'lucide-vue-next'
import type { AudienciaCompletaMT, ContactoMT, ResultadoSincronizacionMT } from '../types/mailerturbo'
import { sincronizarContactos } from '../services/mailerturbo.api'
import { useCatalogosMailerturbo } from '../composables/useCatalogosMailerturbo'
import CargarBaseContactos from '../components/CargarBaseContactos.vue'

// Sube contactos a una lista de MailerTurbo (crea o actualiza por correo).
// Si se pasan `contactos` (ej. la selección de Audiencias) se usan esos; si no,
// se pide un archivo Excel/CSV.
// Con `audiencia` ("Seleccionar toda la audiencia") se manda el filtro y el backend arma la lista completa.
const props = defineProps<{ contactos?: ContactoMT[]; audiencia?: AudienciaCompletaMT; origen?: string; idListaInicial?: number }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ subido: [ResultadoSincronizacionMT] }>()

const nf = new Intl.NumberFormat('es-CO')
const { listas, cargando: cargandoCatalogos, error: errorCatalogos, cargar, nuevaLista } = useCatalogosMailerturbo()

const modoLista = ref<'existente' | 'nueva'>('existente')
const idLista = ref<number | null>(null)
const tituloNuevaLista = ref('')
const etiquetasTexto = ref('')
const contactosArchivo = ref<ContactoMT[]>([])
const subiendo = ref(false)
const error = ref<string | null>(null)
const resultado = ref<ResultadoSincronizacionMT | null>(null)

const desdeSeleccion = computed(() => !!props.contactos || !!props.audiencia)
const contactos = computed(() => props.contactos ?? contactosArchivo.value)
const totalASubir = computed(() => props.audiencia?.total ?? contactos.value.length)
const listasActivas = computed(() => listas.value.filter(l => l.estado === 'Activa'))

watch(visible, (v) => {
  if (!v) return
  modoLista.value = 'existente'
  idLista.value = props.idListaInicial ?? null
  tituloNuevaLista.value = ''
  etiquetasTexto.value = ''
  contactosArchivo.value = []
  error.value = null
  resultado.value = null
  void cargar()
})

const listaValida = computed(() =>
  modoLista.value === 'existente' ? idLista.value !== null : tituloNuevaLista.value.trim().length > 0,
)
const puedeSubir = computed(() => totalASubir.value > 0 && listaValida.value && !subiendo.value)

async function subir() {
  if (!puedeSubir.value) return
  subiendo.value = true
  error.value = null
  try {
    const destino = modoLista.value === 'nueva'
      ? (await nuevaLista(tituloNuevaLista.value)).id
      : idLista.value!
    const etiquetas = etiquetasTexto.value.split(',').map(s => s.trim()).filter(Boolean)
    resultado.value = await sincronizarContactos(
      props.audiencia
        ? { idLista: destino, audiencia: props.audiencia.filtros, etiquetas }
        : { idLista: destino, contactos: contactos.value, etiquetas },
    )
    emit('subido', resultado.value)
    void cargar(true) // refresca los totales de las listas
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudieron subir los contactos.'
  } finally {
    subiendo.value = false
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="surface-card rounded-2xl shadow-2xl w-full max-w-lg flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div>
          <h3 class="text-[14px] font-bold text-heading">Subir contactos a MailerTurbo</h3>
          <p class="text-[11px] text-muted mt-0.5">
            <template v-if="audiencia"><strong class="text-heading">{{ nf.format(audiencia.total) }}</strong> personas (toda la audiencia) · {{ origen || 'selección actual' }}</template>
            <template v-else-if="desdeSeleccion"><strong class="text-heading">{{ nf.format(contactos.length) }}</strong> con correo · {{ origen || 'selección actual' }}</template>
            <template v-else>Desde un archivo Excel o CSV</template>
          </p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-4 overflow-y-auto max-h-[70vh]">
        <div v-if="resultado" class="space-y-2">
          <div class="rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 px-4 py-3 text-[12px] text-emerald-700 dark:text-emerald-300 flex items-start gap-2">
            <Check :size="15" class="mt-0.5 shrink-0" />
            <span>
              {{ nf.format(resultado.creados) }} creados y {{ nf.format(resultado.actualizados) }} actualizados
              de {{ nf.format(resultado.total) }}.
            </span>
          </div>
          <div v-if="resultado.fallos.length" class="rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-[11px] text-amber-700 dark:text-amber-300">
            <div class="flex items-center gap-1.5 font-semibold"><AlertTriangle :size="13" /> {{ resultado.fallos.length }} no se pudieron subir</div>
            <ul class="mt-1 space-y-0.5 max-h-32 overflow-y-auto">
              <li v-for="f in resultado.fallos" :key="f.correo"><strong>{{ f.correo }}</strong> — {{ f.error }}</li>
            </ul>
          </div>
        </div>

        <template v-else>
          <div v-if="!desdeSeleccion">
            <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Base de contactos</label>
            <CargarBaseContactos v-model="contactosArchivo" />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Lista de destino</label>
            <div class="grid grid-cols-2 gap-2 mb-2">
              <button
                type="button" @click="modoLista = 'existente'"
                class="h-8 rounded-lg border text-[11px] font-semibold transition-all"
                :class="modoLista === 'existente' ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 font-bold dark:text-white' : 'border-default bg-white dark:bg-slate-800 text-body'"
              >Lista existente</button>
              <button
                type="button" @click="modoLista = 'nueva'"
                class="h-8 rounded-lg border text-[11px] font-semibold transition-all"
                :class="modoLista === 'nueva' ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 font-bold dark:text-white' : 'border-default bg-white dark:bg-slate-800 text-body'"
              >Crear lista nueva</button>
            </div>
            <div v-if="modoLista === 'existente'">
              <div v-if="cargandoCatalogos" class="flex items-center gap-2 text-[11px] text-muted h-9"><Loader2 :size="13" class="animate-spin" /> Cargando listas…</div>
              <select
                v-else
                v-model="idLista"
                class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none cursor-pointer focus:border-[#2447F9]"
              >
                <option :value="null" disabled>Elige una lista…</option>
                <option v-for="l in listasActivas" :key="l.id" :value="l.id">{{ l.titulo }} ({{ nf.format(l.totalCorreos) }})</option>
              </select>
            </div>
            <input
              v-else
              v-model="tituloNuevaLista"
              placeholder="Nombre de la lista (ej. Afiliados Pereira sin uso)"
              class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]"
            />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Etiquetas <span class="normal-case font-normal text-muted">(opcional, separadas por coma)</span></label>
            <input
              v-model="etiquetasTexto"
              placeholder="crm, plan-liga"
              class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]"
            />
          </div>

          <div v-if="errorCatalogos || error" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">
            {{ error || errorCatalogos }}
          </div>

          <p class="text-[10px] text-muted">
            Si el correo ya existe en MailerTurbo, solo se agrega a la lista (sin cambiar sus datos ni quitarlo de otras listas).
            <template v-if="audiencia"> Las personas sin correo válido se omiten. Con audiencias grandes puede tardar unos minutos.</template>
          </p>
        </template>
      </div>

      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-default surface-header">
        <button @click="visible = false" class="h-9 px-5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
          {{ resultado ? 'Cerrar' : 'Cancelar' }}
        </button>
        <button
          v-if="!resultado"
          @click="subir"
          :disabled="!puedeSubir"
          class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50"
        >
          <Loader2 v-if="subiendo" :size="13" class="animate-spin" /><CloudUpload v-else :size="13" />
          {{ subiendo ? 'Subiendo…' : `Subir (${audiencia ? '~' : ''}${nf.format(totalASubir)})` }}
        </button>
      </div>
    </div>
  </div>
</template>
