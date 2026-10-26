<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  X, Send, Check, Loader2, Users, ListChecks, FileSpreadsheet, LayoutTemplate, FileCode2, PenLine, CalendarClock, Search, Eye, RefreshCw,
} from 'lucide-vue-next'
import type { AudienciaCompletaMT, ContactoMT, EnvioCampanaMT, ResultadoEnvioCampanaMT } from '../types/mailerturbo'
import { enviarCampana } from '../services/mailerturbo.api'
import { useCatalogosMailerturbo } from '../composables/useCatalogosMailerturbo'
import { usePlantillas } from '@/features/campanas/composables/usePlantillas'
import CargarBaseContactos from '../components/CargarBaseContactos.vue'
import ConfirmDialog from '@/features/embudos/components/ConfirmDialog.vue'
import DisenarMensajeDialog from './DisenarMensajeDialog.vue'

// Crea y envía (o programa) una campaña de correo en MailerTurbo.
// - Destinatarios: la selección que llega por props (Audiencias), listas de
//   MailerTurbo o una base Excel/CSV.
// - Contenido (EnviarCampanaEmail): idplantilla de MailerTurbo, una plantilla
//   del CRM, o el HTML del editor sencillo embebido.
const props = defineProps<{
  contactos?: ContactoMT[]
  /** "Seleccionar toda la audiencia": se manda el filtro y el backend arma la lista. */
  audiencia?: AudienciaCompletaMT
  /** Texto para el encabezado, ej. "Audiencia: Plan Liga · Pereira". */
  origen?: string
  /** Si se abre desde una plantilla del CRM, viene preseleccionada. */
  plantillaCrm?: { nombre: string; asunto: string; html: string } | null
  /** Con qué fuente de destinatarios abre (ej. 'archivo' para "Cargar Excel y enviar"). */
  fuenteInicial?: 'listas' | 'archivo'
  /** Listas marcadas al abrir (ej. "Enviar campaña a esta lista"). */
  idListasIniciales?: number[]
}>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ enviada: [ResultadoEnvioCampanaMT] }>()

const nf = new Intl.NumberFormat('es-CO')
const { listas, plantillas: plantillasMT, perfiles, cargando: cargandoCatalogos, error: errorCatalogos, cargar } = useCatalogosMailerturbo()
const { plantillas: plantillasCrm, refrescar: refrescarPlantillasCrm } = usePlantillas()

type FuenteDestinatarios = 'seleccion' | 'listas' | 'archivo'
type FuenteContenido = 'mailerturbo' | 'crm' | 'diseno'

const fuente = ref<FuenteDestinatarios>('listas')
const idListas = ref<number[]>([])
const busquedaLista = ref('')
const contactosArchivo = ref<ContactoMT[]>([])
const nombreLista = ref('')

const fuenteContenido = ref<FuenteContenido>('mailerturbo')
const idPlantillaMT = ref<number | null>(null)
const idPlantillaCrm = ref('')
const htmlDiseno = ref('')
const editorVisible = ref(false)

const idPerfil = ref<number | null>(null)
const nombreCampana = ref('')
const asunto = ref('')
const programar = ref(false)
const fechaProgramacion = ref('')

const verVistaPrevia = ref(false)
const pantallaCompleta = ref(false)
const confirmando = ref(false)
const enviando = ref(false)
const error = ref<string | null>(null)
const resultado = ref<ResultadoEnvioCampanaMT | null>(null)

const hoy = () => new Date().toISOString().slice(0, 10)

watch(visible, (v) => {
  if (!v) return
  fuente.value = props.contactos || props.audiencia ? 'seleccion' : (props.fuenteInicial ?? 'listas')
  idListas.value = [...(props.idListasIniciales ?? [])]
  busquedaLista.value = ''
  contactosArchivo.value = []
  nombreLista.value = ''
  refrescarPlantillasCrm()
  fuenteContenido.value = props.plantillaCrm ? 'crm' : 'mailerturbo'
  idPlantillaMT.value = null
  idPlantillaCrm.value = ''
  htmlDiseno.value = ''
  editorVisible.value = false
  nombreCampana.value = props.plantillaCrm ? `${props.plantillaCrm.nombre} · ${hoy()}` : ''
  asunto.value = props.plantillaCrm?.asunto ?? ''
  programar.value = false
  fechaProgramacion.value = ''
  verVistaPrevia.value = false
  pantallaCompleta.value = false
  confirmando.value = false
  error.value = null
  resultado.value = null
  void cargar().then(() => {
    if (idPerfil.value === null && perfiles.value.length) idPerfil.value = perfiles.value[0].id
  })
})

// ── Destinatarios ────────────────────────────────────────────────────
const listasActivas = computed(() => listas.value.filter(l => l.estado === 'Activa'))
const listasFiltradas = computed(() => {
  const q = busquedaLista.value.trim().toLowerCase()
  return q ? listasActivas.value.filter(l => l.titulo.toLowerCase().includes(q)) : listasActivas.value
})
const toggleLista = (id: number) => {
  idListas.value = idListas.value.includes(id) ? idListas.value.filter(x => x !== id) : [...idListas.value, id]
}

const contactosEnvio = computed<ContactoMT[]>(() =>
  fuente.value === 'seleccion' ? (props.contactos ?? []) : fuente.value === 'archivo' ? contactosArchivo.value : [],
)
/** Aproximado para listas (MailerTurbo descarta luego duplicados, rebotes y bajas). */
const usaAudiencia = computed(() => fuente.value === 'seleccion' && !!props.audiencia)
const totalSeleccion = computed(() => props.audiencia?.total ?? props.contactos?.length ?? 0)
const totalDestinatarios = computed(() =>
  fuente.value === 'listas'
    ? listas.value.filter(l => idListas.value.includes(l.id)).reduce((s, l) => s + l.totalActivos, 0)
    : usaAudiencia.value ? totalSeleccion.value : contactosEnvio.value.length,
)
/** Aproximado: listas (MailerTurbo descarta rebotes/bajas) o toda la audiencia (el backend descarta sin correo). */
const totalAproximado = computed(() => fuente.value === 'listas' || usaAudiencia.value)
const destinatariosListos = computed(() =>
  fuente.value === 'listas' ? idListas.value.length > 0 : totalDestinatarios.value > 0,
)

// ── Contenido ────────────────────────────────────────────────────────
const plantillaCrmElegida = computed(() =>
  props.plantillaCrm ?? plantillasCrm.value.find(p => p.id === idPlantillaCrm.value) ?? null,
)
watch(idPlantillaCrm, () => {
  const p = plantillaCrmElegida.value
  if (!p) return
  if (!asunto.value.trim()) asunto.value = p.asunto
  if (!nombreCampana.value.trim()) nombreCampana.value = `${p.nombre} · ${hoy()}`
})
watch(idPlantillaMT, (id) => {
  const p = plantillasMT.value.find(x => x.id === id)
  if (p && !nombreCampana.value.trim()) nombreCampana.value = `${p.nombre} · ${hoy()}`
})
const disenoListo = computed(() => {
  const html = htmlDiseno.value
  return /<img\b/i.test(html) || html.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim().length > 0
})
const htmlVistaPrevia = computed(() =>
  fuenteContenido.value === 'diseno' ? htmlDiseno.value
    : fuenteContenido.value === 'crm' ? (plantillaCrmElegida.value?.html ?? '')
      : '',
)
const puedeVerVista = computed(() =>
  (fuenteContenido.value === 'diseno' && disenoListo.value)
  || (fuenteContenido.value === 'crm' && !!plantillaCrmElegida.value?.html),
)

function abrirVistaPrevia() {
  if (verVistaPrevia.value) {
    verVistaPrevia.value = false
    pantallaCompleta.value = false
    return
  }
  pantallaCompleta.value = false
  verVistaPrevia.value = true
}

const contenidoListo = computed(() =>
  fuenteContenido.value === 'mailerturbo' ? idPlantillaMT.value !== null
    : fuenteContenido.value === 'diseno' ? disenoListo.value
      : !!plantillaCrmElegida.value?.html,
)

function abrirDiseno() {
  fuenteContenido.value = 'diseno'
  editorVisible.value = true
}

function alGuardarDiseno(payload: { html: string; cerrar: boolean }) {
  htmlDiseno.value = payload.html
}

// ── Envío ────────────────────────────────────────────────────────────
const fechaValida = computed(() => !programar.value || (!!fechaProgramacion.value && new Date(fechaProgramacion.value) > new Date()))
const puedeEnviar = computed(() =>
  destinatariosListos.value && contenidoListo.value && idPerfil.value !== null
  && !!nombreCampana.value.trim() && !!asunto.value.trim() && fechaValida.value && !enviando.value,
)

const mensajeConfirmacion = computed(() => {
  const cuando = programar.value ? `se programará para el ${fechaProgramacion.value.replace('T', ' ')}` : 'se enviará de inmediato'
  const quienes = fuente.value === 'listas'
    ? `${idListas.value.length} lista(s) (~${nf.format(totalDestinatarios.value)} contactos activos)`
    : usaAudiencia.value
      ? `toda la audiencia (${nf.format(totalDestinatarios.value)} personas; se omiten las que no tengan correo válido)`
      : `${nf.format(totalDestinatarios.value)} contacto(s)`
  return `La campaña "${nombreCampana.value.trim()}" ${cuando} a ${quienes}. ¿Continuar?`
})

async function enviar() {
  if (!puedeEnviar.value) return
  enviando.value = true
  error.value = null
  const envio: EnvioCampanaMT = {
    nombre: nombreCampana.value,
    asunto: asunto.value,
    idPerfilEnvio: idPerfil.value!,
    contenido: fuenteContenido.value === 'mailerturbo'
      ? { tipo: 'plantilla_mailerturbo', idPlantilla: idPlantillaMT.value! }
      : { tipo: 'html', html: fuenteContenido.value === 'diseno' ? htmlDiseno.value : plantillaCrmElegida.value!.html },
    destinatarios: fuente.value === 'listas'
      ? { tipo: 'listas', idListas: idListas.value }
      : usaAudiencia.value
        ? { tipo: 'audiencia', filtros: props.audiencia!.filtros, nombreLista: nombreLista.value }
        : { tipo: 'contactos', contactos: contactosEnvio.value, nombreLista: nombreLista.value },
    fechaProgramacion: programar.value ? `${fechaProgramacion.value.replace('T', ' ')}:00` : null,
  }
  try {
    resultado.value = await enviarCampana(envio)
    emit('enviada', resultado.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo enviar la campaña.'
  } finally {
    enviando.value = false
    confirmando.value = false
  }
}

const claseOpcion = (activa: boolean) => activa
  ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 font-bold dark:text-white'
  : 'border-default bg-white dark:bg-slate-800 text-body hover:bg-slate-50 dark:hover:bg-slate-700'
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="surface-card rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col overflow-hidden max-h-[92vh]">
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div class="min-w-0">
          <h3 class="text-[14px] font-bold text-heading">Campaña de correo · MailerTurbo</h3>
          <p class="text-[11px] text-muted mt-0.5 truncate">{{ origen || 'Envío masivo con seguimiento de aperturas y clics' }}</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400 shrink-0"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-5 overflow-y-auto">
        <!-- Resultado -->
        <div v-if="resultado" class="rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 px-4 py-3 text-[12px] text-emerald-700 dark:text-emerald-300 flex items-start gap-2">
          <Check :size="15" class="mt-0.5 shrink-0" />
          <span>
            Campaña <strong>#{{ resultado.idCampana }}</strong> creada en MailerTurbo<template v-if="resultado.totalContactos !== null"> para <strong>{{ nf.format(resultado.totalContactos) }}</strong> contacto(s) con correo</template>.
            <span v-if="resultado.explicacion" class="block text-[11px] opacity-80 mt-0.5">{{ resultado.explicacion }}</span>
          </span>
        </div>

        <template v-else>
          <div v-if="cargandoCatalogos" class="flex items-center gap-2 text-[11px] text-muted"><Loader2 :size="13" class="animate-spin" /> Cargando listas, plantillas y remitentes de MailerTurbo…</div>
          <div v-if="errorCatalogos" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">{{ errorCatalogos }}</div>

          <!-- 1. Destinatarios -->
          <section class="space-y-2">
            <h4 class="text-[11px] font-bold text-body uppercase tracking-wide">1 · Destinatarios</h4>
            <div class="grid gap-2" :class="contactos || audiencia ? 'grid-cols-3' : 'grid-cols-2'">
              <button v-if="contactos || audiencia" type="button" @click="fuente = 'seleccion'" class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-semibold transition-all" :class="claseOpcion(fuente === 'seleccion')">
                <Users :size="13" /> {{ audiencia ? 'Toda la audiencia' : 'Selección' }} ({{ nf.format(totalSeleccion) }})
              </button>
              <button type="button" @click="fuente = 'listas'" class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-semibold transition-all" :class="claseOpcion(fuente === 'listas')">
                <ListChecks :size="13" /> Listas MailerTurbo
              </button>
              <button type="button" @click="fuente = 'archivo'" class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-semibold transition-all" :class="claseOpcion(fuente === 'archivo')">
                <FileSpreadsheet :size="13" /> Archivo Excel/CSV
              </button>
            </div>

            <div v-if="fuente === 'listas'" class="rounded-lg border border-default overflow-hidden">
              <div class="flex items-center gap-2 px-3 h-9 border-b border-default">
                <Search :size="13" class="text-muted shrink-0" />
                <input v-model="busquedaLista" placeholder="Buscar lista…" class="flex-1 bg-transparent text-[12px] outline-none text-body" />
              </div>
              <div class="max-h-40 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700">
                <label v-for="l in listasFiltradas" :key="l.id" class="flex items-center gap-2 px-3 py-2 text-[12px] cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
                  <input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9]" :checked="idListas.includes(l.id)" @change="toggleLista(l.id)" />
                  <span class="flex-1 truncate text-body">{{ l.titulo }}</span>
                  <span class="text-[11px] text-muted tabular-nums">{{ nf.format(l.totalActivos) }} activos</span>
                </label>
                <p v-if="!listasFiltradas.length && !cargandoCatalogos" class="px-3 py-4 text-center text-[11px] text-muted">No hay listas que coincidan.</p>
              </div>
            </div>

            <CargarBaseContactos v-else-if="fuente === 'archivo'" v-model="contactosArchivo" />

            <p v-if="usaAudiencia" class="text-[11px] text-muted">
              Se envía a todas las personas del filtro, incluidas las páginas que no se han cargado. Las que no tengan correo válido o lo tengan repetido se omiten.
            </p>

            <input
              v-if="fuente !== 'listas'"
              v-model="nombreLista"
              placeholder="Nombre de la lista que se crea en MailerTurbo (opcional)"
              class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]"
            />
          </section>

          <!-- 2. Contenido -->
          <section class="space-y-2">
            <h4 class="text-[11px] font-bold text-body uppercase tracking-wide">2 · Contenido</h4>
            <div v-if="!plantillaCrm" class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <button type="button" @click="fuenteContenido = 'mailerturbo'" class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-semibold transition-all" :class="claseOpcion(fuenteContenido === 'mailerturbo')">
                <LayoutTemplate :size="13" /> Plantilla MailerTurbo
              </button>
              <button type="button" @click="fuenteContenido = 'crm'" class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-semibold transition-all" :class="claseOpcion(fuenteContenido === 'crm')">
                <FileCode2 :size="13" /> Plantilla del CRM
              </button>
              <button type="button" @click="abrirDiseno" class="flex items-center justify-center gap-1.5 h-9 rounded-lg border text-[11px] font-semibold transition-all" :class="claseOpcion(fuenteContenido === 'diseno')">
                <PenLine :size="13" /> Diseñar el correo
              </button>
            </div>

            <button
              v-if="puedeVerVista"
              type="button"
              class="flex items-center justify-center gap-1.5 h-9 px-3 rounded-lg border text-[11px] font-semibold transition-all"
              :class="claseOpcion(verVistaPrevia)"
              @click="abrirVistaPrevia"
            ><Eye :size="13" /> Vista previa</button>

            <div v-if="fuenteContenido === 'mailerturbo'" class="space-y-2">
              <select
                v-model="idPlantillaMT"
                class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none cursor-pointer focus:border-[#2447F9]"
              >
                <option :value="null" disabled>Elige una plantilla de MailerTurbo…</option>
                <option v-for="p in plantillasMT" :key="p.id" :value="p.id">{{ p.nombre }}</option>
              </select>
              <p class="text-[11px] text-muted">
                <button type="button" class="inline-flex items-center gap-1 font-semibold text-[#2447F9] hover:underline" @click="cargar(true)">
                  <RefreshCw :size="11" /> Actualizar plantillas
                </button>
              </p>
            </div>

            <template v-else-if="fuenteContenido === 'crm'">
              <div v-if="plantillaCrm" class="flex items-center gap-2 px-3 h-9 rounded-lg border border-default text-[12px] text-body">
                <FileCode2 :size="13" class="text-[#7C3AED] shrink-0" /><span class="truncate">{{ plantillaCrm.nombre }}</span>
              </div>
              <select
                v-else
                v-model="idPlantillaCrm"
                class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none cursor-pointer focus:border-[#2447F9]"
              >
                <option value="" disabled>Elige una plantilla del editor del CRM…</option>
                <option v-for="p in plantillasCrm" :key="p.id" :value="p.id">{{ p.nombre }}</option>
              </select>
            </template>
          </section>

          <!-- 3. Datos de la campaña -->
          <section class="space-y-3">
            <h4 class="text-[11px] font-bold text-body uppercase tracking-wide">3 · Datos de la campaña</h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-1">Nombre (interno)</label>
                <input v-model="nombreCampana" placeholder="Ej. Recordatorio uso Plan Liga" class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]" />
              </div>
              <div>
                <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-1">Remitente</label>
                <select v-model="idPerfil" class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none cursor-pointer focus:border-[#2447F9]">
                  <option :value="null" disabled>Elige un perfil de envío…</option>
                  <option v-for="p in perfiles" :key="p.id" :value="p.id">{{ p.titulo }} — {{ p.correo }}</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-[10px] font-bold text-subtle uppercase tracking-wide mb-1">Asunto</label>
              <input v-model="asunto" placeholder="Lo que verá la persona en su bandeja" class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]" />
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <label class="flex items-center gap-2 text-[12px] text-body cursor-pointer">
                <input type="checkbox" v-model="programar" class="w-3.5 h-3.5 accent-[#2447F9]" />
                <CalendarClock :size="13" /> Programar envío
              </label>
              <input
                v-if="programar"
                v-model="fechaProgramacion"
                type="datetime-local"
                class="h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]"
              />
              <span v-if="programar && fechaProgramacion && !fechaValida" class="text-[11px] text-red-500">La fecha debe ser futura.</span>
            </div>
          </section>

          <div v-if="error" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">{{ error }}</div>
        </template>
      </div>

      <div class="flex items-center justify-between gap-2 px-6 py-4 border-t border-default surface-header">
        <span v-if="!resultado" class="text-[11px] text-muted">
          <template v-if="totalAproximado">~</template><strong class="text-heading tabular-nums">{{ nf.format(totalDestinatarios) }}</strong> destinatario(s)
        </span>
        <span v-else />
        <div class="flex items-center gap-2">
          <button @click="visible = false" class="h-9 px-5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
            {{ resultado ? 'Cerrar' : 'Cancelar' }}
          </button>
          <button
            v-if="!resultado"
            @click="confirmando = true"
            :disabled="!puedeEnviar"
            class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50"
          >
            <Send :size="13" /> {{ programar ? 'Programar' : 'Enviar' }}
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="visible && verVistaPrevia && htmlVistaPrevia"
        class="fixed inset-0 z-[100002] flex items-center justify-center bg-[#1e3a8a]/40"
        :class="pantallaCompleta ? 'p-0' : 'p-6 sm:p-10'"
      >
        <div
          class="flex w-full flex-col overflow-hidden bg-white shadow-2xl"
          :class="pantallaCompleta ? 'h-full max-w-none rounded-none' : 'h-full max-h-[820px] max-w-6xl rounded-2xl'"
        >
          <div class="flex shrink-0 items-center gap-2 border-b border-slate-200 px-5 py-3">
            <h3 class="text-[22px] font-semibold tracking-tight text-[#243056]">Vista previa</h3>
            <button
              type="button"
              class="ml-auto h-9 px-3 rounded-lg border border-default bg-white text-[11px] font-semibold text-body hover:bg-slate-50"
              @click="pantallaCompleta = !pantallaCompleta"
            >{{ pantallaCompleta ? 'Ventana del editor' : 'Pantalla completa' }}</button>
            <button type="button" class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" aria-label="Cerrar" @click="abrirVistaPrevia">
              <X :size="18" />
            </button>
          </div>
          <iframe
            :srcdoc="htmlVistaPrevia"
            sandbox=""
            class="min-h-0 w-full flex-1 border-0 bg-white"
            title="Vista previa del correo"
          />
        </div>
      </div>
    </Teleport>

    <DisenarMensajeDialog
      v-model:visible="editorVisible"
      :html="htmlDiseno"
      @guardar="alGuardarDiseno"
    />

    <ConfirmDialog
      :visible="confirmando"
      titulo="Confirmar campaña"
      :mensaje="mensajeConfirmacion"
      :texto-confirmar="programar ? 'Programar' : 'Enviar'"
      :cargando="enviando"
      @confirmar="enviar"
      @cancelar="confirmando = false"
    />
  </div>
</template>
