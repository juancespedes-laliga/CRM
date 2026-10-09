<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { ArrowLeft, Save, Download, Send, Check, Eye, Maximize2, Minimize2, Upload, FileText, Mail } from 'lucide-vue-next'
import type { Plantilla, PlantillaDraft } from '../types/plantilla'
import { descargarHtml } from '../constants/campanas.constants'
import EditorHtmlGrapes from '../components/EditorHtmlGrapes.vue'

const props = defineProps<{ plantilla: Plantilla | null }>()
const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ submit: [PlantillaDraft]; enviar: [PlantillaDraft] }>()

const raiz = ref<HTMLDivElement>()
const fileInput = ref<HTMLInputElement>()
const editorRef = ref<InstanceType<typeof EditorHtmlGrapes>>()
const nombre = ref('')
const asunto = ref('')
const guardado = ref(false)
const errorNombre = ref(false)
const enPantallaCompleta = ref(false)

watch(visible, (v) => {
  if (v) {
    nombre.value = props.plantilla?.nombre ?? ''
    asunto.value = props.plantilla?.asunto ?? ''
    guardado.value = false
    errorNombre.value = false
    document.addEventListener('fullscreenchange', onFsChange)
  } else {
    document.removeEventListener('fullscreenchange', onFsChange)
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
  }
})
const onFsChange = () => { enPantallaCompleta.value = !!document.fullscreenElement }
onBeforeUnmount(() => document.removeEventListener('fullscreenchange', onFsChange))

function armarDraft(): PlantillaDraft | null {
  const ed = editorRef.value
  if (!ed || !nombre.value.trim()) return null
  const asuntoTxt = asunto.value.trim() || nombre.value.trim()
  return {
    nombre: nombre.value.trim(),
    asunto: asunto.value.trim(),
    html: ed.getDocumento(asuntoTxt),   // un solo archivo HTML, estilos embebidos
    css: ed.getCss(),                   // interno, para reabrir sin perder estilos
    proyecto: ed.getProjectData(),
  }
}

function guardar() {
  const draft = armarDraft()
  if (!draft) { errorNombre.value = true; return }
  errorNombre.value = false
  emit('submit', draft)
  guardado.value = true
  setTimeout(() => { guardado.value = false }, 2500)
}

function descargar() {
  const ed = editorRef.value
  if (!ed) return
  descargarHtml(nombre.value || 'plantilla', ed.getDocumento(asunto.value || nombre.value || 'Correo'))
}

function enviar() {
  const draft = armarDraft()
  if (!draft) { errorNombre.value = true; return }
  errorNombre.value = false
  // Solo 'enviar': el padre (List.vue) guarda este draft y, ya guardado,
  // abre el dialogo de envio. Emitir tambien 'submit' aca duplicaria el
  // guardado (dos POST/PUT contra el backend por un solo click).
  emit('enviar', draft)
}

function importarArchivo(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { editorRef.value?.setDocumento(String(reader.result ?? '')) }
  reader.readAsText(file)
  ;(e.target as HTMLInputElement).value = ''
}

function togglePantallaCompleta() {
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
  else raiz.value?.requestFullscreen().catch(() => {})
}
</script>

<template>
  <div v-if="visible" ref="raiz" class="fixed inset-0 z-[99998] flex flex-col bg-white dark:bg-slate-900">
    <!-- Barra superior -->
    <div class="flex items-center gap-2 px-3 md:px-4 h-14 border-b border-default surface-header shrink-0">
      <button
        @click="visible = false"
        class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-bold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all shrink-0"
      ><ArrowLeft :size="14" /> Volver</button>

      <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-2 min-w-0">
        <!-- Nombre interno de la plantilla (solo lo ve el equipo) -->
        <div
          class="flex items-center h-9 rounded-lg border bg-slate-50 dark:bg-slate-800 overflow-hidden transition-all"
          :class="errorNombre ? 'border-red-400 dark:border-red-500' : 'border-slate-200 dark:border-slate-600 focus-within:border-[#2447F9]'"
        >
          <span class="shrink-0 self-stretch px-2.5 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-subtle bg-slate-100 dark:bg-slate-700/60 border-r border-slate-200 dark:border-slate-600">
            <FileText :size="12" /> Plantilla
          </span>
          <input
            v-model="nombre"
            placeholder="Nombre para identificarla (uso interno) *"
            title="Nombre de la plantilla: solo lo ve el equipo, no se envía en el correo"
            class="flex-1 min-w-0 h-full px-3 bg-transparent text-[12px] font-semibold text-slate-900 dark:text-slate-100 outline-none"
          />
        </div>
        <!-- Asunto: lo que ve el destinatario en su bandeja -->
        <div class="flex items-center h-9 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 overflow-hidden focus-within:border-[#2447F9] transition-all">
          <span class="shrink-0 self-stretch px-2.5 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-subtle bg-slate-100 dark:bg-slate-700/60 border-r border-slate-200 dark:border-slate-600">
            <Mail :size="12" /> Asunto
          </span>
          <input
            v-model="asunto"
            placeholder="Lo que verá el destinatario en su bandeja"
            title="Asunto del correo: es el texto que aparece en la bandeja de entrada de quien lo recibe"
            class="flex-1 min-w-0 h-full px-3 bg-transparent text-[12px] text-slate-900 dark:text-slate-100 outline-none"
          />
        </div>
      </div>

      <div class="flex items-center gap-1.5 shrink-0">
        <input ref="fileInput" type="file" accept=".html,text/html" class="hidden" @change="importarArchivo" />
        <button
          @click="fileInput?.click()"
          title="Importar un archivo .html"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        ><Upload :size="13" /> Importar</button>
        <button
          @click="editorRef?.vistaPrevia()"
          title="Vista previa"
          class="hidden md:flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        ><Eye :size="13" /> Previa</button>
        <button
          @click="descargar"
          title="Descargar el archivo .html"
          class="hidden sm:flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        ><Download :size="13" /> Descargar</button>
        <button
          @click="togglePantallaCompleta"
          :title="enPantallaCompleta ? 'Salir de pantalla completa' : 'Pantalla completa'"
          class="hidden sm:flex w-9 h-9 rounded-lg border border-default bg-white dark:bg-slate-800 items-center justify-center text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        ><component :is="enPantallaCompleta ? Minimize2 : Maximize2" :size="14" /></button>
        <button
          @click="enviar"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-[#2447F9]/30 bg-[#EEF2FF] dark:bg-blue-950/40 text-[11px] font-bold text-slate-900 dark:text-white hover:bg-[#E0E7FF] dark:hover:bg-blue-950/60 transition-all"
        ><Send :size="13" /> Enviar</button>
        <button
          @click="guardar"
          class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all"
        >
          <component :is="guardado ? Check : Save" :size="14" />
          {{ guardado ? 'Guardado' : 'Guardar' }}
        </button>
      </div>
    </div>

    <p v-if="errorNombre" class="px-4 py-1.5 text-[11px] text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 shrink-0">
      Ponle un nombre a la plantilla antes de guardar o enviar.
    </p>

    <!-- Editor visual -->
    <div class="flex-1 min-h-0 relative">
      <EditorHtmlGrapes ref="editorRef" :plantilla="plantilla" />
    </div>
  </div>
</template>
