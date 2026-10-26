<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Loader2, X } from 'lucide-vue-next'
import { getEditorPlus, type TagEditorMT } from '../services/mailerturbo.api'

// Editor sencillo de MailerTurbo (TinyMCE), embebido al diseñar el correo.
// El plus no se carga: su licencia solo responde "authorize" fuera de su sitio.
const visible = defineModel<boolean>('visible', { required: true })

const props = defineProps<{ html?: string }>()
const emit = defineEmits<{ guardar: [payload: { html: string; cerrar: boolean }] }>()

const ID_TINY = 'crm-editor-sencillo'
const TINYMCE_BASE = 'https://cdn.jsdelivr.net/npm/tinymce@6.8.3'

interface TinyEditor {
  getContent: () => string
  setContent: (html: string) => void
  remove: () => void
  insertContent: (html: string) => void
  getWin: () => Window | null
  on: (evento: string, fn: () => void) => void
  ui: { registry: { addButton: (nombre: string, spec: unknown) => void; addMenuButton: (nombre: string, spec: unknown) => void } }
}
interface TinyApi {
  init: (opciones: Record<string, unknown>) => Promise<TinyEditor[]>
  get: (id: string) => TinyEditor | null
}

const cargando = ref(false)
const guardado = ref(false)
const error = ref<string | null>(null)
const htmlLocal = ref('')
let generacion = 0

const scripts = new Map<string, Promise<void>>()

function cargarScript(src: string): Promise<void> {
  const previo = scripts.get(src)
  if (previo) return previo
  const promesa = new Promise<void>((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve()
      return
    }
    const etiqueta = document.createElement('script')
    etiqueta.src = src
    etiqueta.async = true
    etiqueta.onload = () => resolve()
    etiqueta.onerror = () => reject(new Error('No se pudo cargar el editor.'))
    document.head.appendChild(etiqueta)
  })
  scripts.set(src, promesa)
  return promesa
}

function tinyApi(): TinyApi | undefined {
  return (window as unknown as { tinymce?: TinyApi }).tinymce
}

function gruposDe(tags: TagEditorMT[]): Map<string, TagEditorMT[]> {
  const grupos = new Map<string, TagEditorMT[]>()
  for (const tag of tags) {
    const lista = grupos.get(tag.grupo) ?? []
    lista.push(tag)
    grupos.set(tag.grupo, lista)
  }
  return grupos
}

function destruir() {
  try { tinyApi()?.get(ID_TINY)?.remove() } catch { /* el editor ya no estaba */ }
}

async function iniciar(tags: TagEditorMT[]) {
  await cargarScript(`${TINYMCE_BASE}/tinymce.min.js`)
  await cargarScript('https://cdn.jsdelivr.net/npm/tinymce-i18n@24.12.9/langs6/es.js')
  const api = tinyApi()
  if (!api) throw new Error('No se pudo cargar el editor sencillo.')
  api.get(ID_TINY)?.remove()
  const grupos = gruposDe(tags)
  await api.init({
    selector: `#${ID_TINY}`,
    base_url: TINYMCE_BASE,
    suffix: '.min',
    language: 'es',
    language_url: 'https://cdn.jsdelivr.net/npm/tinymce-i18n@24.12.9/langs6/es.js',
    height: '100%',
    menubar: 'file edit view insert format tools table',
    toolbar_mode: 'wrap',
    branding: false,
    promotion: false,
    relative_urls: false,
    remove_script_host: false,
    image_advtab: true,
    plugins: [
      'advlist', 'autolink', 'autosave', 'link', 'image', 'lists', 'charmap', 'preview', 'anchor', 'pagebreak',
      'searchreplace', 'wordcount', 'visualblocks', 'visualchars', 'code', 'fullscreen', 'insertdatetime', 'media',
      'nonbreaking', 'table', 'emoticons', 'template', 'codesample', 'directionality',
    ],
    toolbar1: 'bold italic underline strikethrough | fontsize fontfamily | forecolor backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | blockquote',
    toolbar2: 'styles blocks | subscript superscript removeformat | tagsdropdown | cut copy paste | table | link unlink anchor image media code',
    toolbar3: 'hr charmap emoticons | imprimir fullscreen | ltr rtl | visualchars visualblocks nonbreaking template pagebreak restoredraft insertdatetime preview | searchreplace undo redo',
    templates: [
      { title: 'Párrafo', description: 'Texto suelto', content: '<p>Escribe aquí el mensaje.</p>' },
    ],
    font_size_formats: '8pt 10pt 12pt 14pt 18pt 24pt 36pt',
    font_family_formats: 'sans-serif=sans-serif; Arial=arial,helvetica,sans-serif; Georgia=georgia,palatino,serif; Times New Roman=times new roman,times,serif; Courier New=courier new,courier,monospace; Verdana=verdana,geneva,sans-serif; Tahoma=tahoma,arial,helvetica,sans-serif; Trebuchet MS=trebuchet ms,geneva,sans-serif',
    style_formats_merge: true,
    style_formats: [
      {
        title: 'Estilos de botón',
        items: [
          { title: 'Botón azul', inline: 'span', styles: { color: '#fff', backgroundColor: '#0000FF', padding: '10px', borderRadius: '5px' } },
          { title: 'Botón verde', inline: 'span', styles: { color: '#fff', backgroundColor: '#008000', padding: '10px', borderRadius: '5px' } },
          { title: 'Botón amarillo', inline: 'span', styles: { color: '#000', backgroundColor: '#FFFF00', padding: '10px', borderRadius: '5px' } },
          { title: 'Botón naranja', inline: 'span', styles: { color: '#fff', backgroundColor: '#FFA500', padding: '10px', borderRadius: '5px' } },
          { title: 'Botón gris', inline: 'span', styles: { color: '#fff', backgroundColor: '#A9A9A9', padding: '10px', borderRadius: '5px' } },
        ],
      },
    ],
    content_style: 'body { font-family: sans-serif; font-size: 12pt; }',
    setup: (editor: TinyEditor) => {
      editor.ui.registry.addButton('imprimir', {
        icon: 'print',
        tooltip: 'Imprimir',
        onAction: () => editor.getWin()?.print(),
      })
      editor.ui.registry.addMenuButton('tagsdropdown', {
        text: 'Insertar Tag',
        fetch: (callback: (items: unknown[]) => void) => {
          callback([...grupos.entries()].map(([nombre, items]) => ({
            type: 'nestedmenuitem',
            text: nombre,
            getSubmenuItems: () => items.map(tag => ({
              type: 'menuitem',
              text: tag.tag.replace(/\{\{|\}\}/g, ''),
              onAction: () => editor.insertContent(tag.tag),
            })),
          })))
        },
      })
      editor.on('init', () => {
        if (htmlLocal.value) editor.setContent(htmlLocal.value)
      })
    },
  })
}

watch(visible, (abierto) => {
  const gen = ++generacion
  destruir()
  error.value = null
  guardado.value = false
  if (!abierto) {
    cargando.value = false
    return
  }
  htmlLocal.value = props.html ?? ''
  cargando.value = true
  void (async () => {
    let tags: TagEditorMT[] = []
    try {
      tags = (await getEditorPlus()).tags
    } catch {
      tags = []
    }
    if (gen !== generacion) return
    await nextTick()
    if (gen !== generacion) return
    await iniciar(tags)
  })()
    .catch(e => { error.value = e instanceof Error ? e.message : 'No se pudo abrir el editor.' })
    .finally(() => { if (gen === generacion) cargando.value = false })
})

function guardar(cerrar: boolean) {
  const editor = tinyApi()?.get(ID_TINY)
  if (!editor) {
    error.value = 'El editor todavía no está listo.'
    return
  }
  const html = editor.getContent()
  htmlLocal.value = html
  emit('guardar', { html, cerrar })
  guardado.value = true
  if (cerrar) visible.value = false
}

function cerrar() {
  visible.value = false
}

onBeforeUnmount(destruir)
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-[100000] flex items-center justify-center bg-[#1e3a8a]/40 p-6 sm:p-10">
      <div class="flex h-full max-h-[820px] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div class="flex shrink-0 items-center gap-4 border-b border-slate-200 px-5 py-3">
          <h3 class="text-[22px] font-semibold tracking-tight text-[#243056]">Diseñar mi mensaje</h3>
          <button type="button" class="ml-auto flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100" aria-label="Cerrar" @click="cerrar">
            <X :size="18" />
          </button>
        </div>

        <div class="editor-sencillo relative min-h-0 flex-1 bg-white">
          <div v-if="cargando" class="absolute inset-0 z-10 flex items-center justify-center gap-2 bg-white/80 text-[13px] text-slate-500">
            <Loader2 :size="16" class="animate-spin" /> Cargando editor…
          </div>
          <p v-if="error" class="absolute inset-x-4 top-3 z-20 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[12px] text-red-600">{{ error }}</p>
          <textarea :id="ID_TINY" class="h-full w-full" />
        </div>

        <div class="flex shrink-0 items-center justify-end gap-2 border-t border-slate-200 px-5 py-3">
          <span v-if="guardado" class="mr-auto text-[12px] font-semibold text-emerald-600">Guardado. Este texto es el que se envía en la campaña.</span>
          <button type="button" class="h-9 rounded-full bg-[#3b82f6] px-5 text-[12px] font-bold uppercase tracking-wide text-white hover:bg-[#2563eb] disabled:opacity-50" :disabled="cargando" @click="guardar(false)">
            Guardar
          </button>
          <button type="button" class="h-9 rounded-full bg-[#2563eb] px-5 text-[12px] font-bold uppercase tracking-wide text-white hover:bg-[#1d4ed8] disabled:opacity-50" :disabled="cargando" @click="guardar(true)">
            Guardar y cerrar
          </button>
          <button type="button" class="h-9 rounded-full bg-[#c5cad3] px-5 text-[12px] font-bold uppercase tracking-wide text-[#3a4150] hover:bg-[#b7bdc8]" @click="cerrar">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style>
/* Los menús y cuadros de TinyMCE se cuelgan en la página, por debajo de este
   diálogo (z-index 100000). Sin esto, Insertar Tag, color, enlace e imagen
   se abren detrás y parece que el botón no hace nada. */
.editor-sencillo .tox-tinymce {
  height: 100% !important;
}
.tox-tinymce-aux,
.tox-dialog-wrap,
.tox-dialog,
.tox-notifications-container,
.tox-silver-sink {
  z-index: 100010 !important;
}
</style>
