<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import grapesjs, { type Editor } from 'grapesjs'
import 'grapesjs/dist/css/grapes.min.css'
import type { Plantilla } from '../types/plantilla'
import { armarDocumentoCorreo, PLANTILLA_HTML_INICIAL } from '../constants/campanas.constants'
import { BLOQUES_CORREO } from '../constants/bloques-correo'

const props = defineProps<{ plantilla: Plantilla | null }>()

// Fuentes "web-safe": vienen preinstaladas en Windows/Mac, así que los
// clientes de correo (Gmail, Outlook…) las respetan. Cualquier otra fuente
// (Google Fonts, etc.) no se puede incrustar en un correo y cada cliente la
// reemplaza por su fuente por defecto — por eso el font-family libre se
// cambia aquí por una lista cerrada de opciones que SÍ se van a ver.
const FUENTES_CORREO = [
  { id: 'Arial, Helvetica, sans-serif', label: 'Arial' },
  { id: 'Helvetica, Arial, sans-serif', label: 'Helvetica' },
  { id: "'Verdana', Geneva, sans-serif", label: 'Verdana' },
  { id: "'Tahoma', Geneva, sans-serif", label: 'Tahoma' },
  { id: "'Trebuchet MS', Helvetica, sans-serif", label: 'Trebuchet MS' },
  { id: "Georgia, 'Times New Roman', Times, serif", label: 'Georgia' },
  { id: "'Times New Roman', Times, serif", label: 'Times New Roman' },
  { id: "'Courier New', Courier, monospace", label: 'Courier New' },
]

// Sectores del panel de estilos (a la derecha).
const SECTORES_ESTILO = [
  {
    name: 'Tipografía',
    open: true,
    buildProps: ['font-family', 'font-size', 'font-weight', 'letter-spacing', 'color', 'line-height', 'text-align'],
    properties: [
      { property: 'font-family', type: 'select', defaults: FUENTES_CORREO[0].id, options: FUENTES_CORREO },
    ],
  },
  { name: 'Fondo y borde', open: false, buildProps: ['background-color', 'border-radius', 'border'] },
  { name: 'Espaciado', open: false, buildProps: ['padding', 'margin'] },
  { name: 'Tamaño', open: false, buildProps: ['width', 'height', 'max-width'] },
]

const el = ref<HTMLDivElement>()
const editor = shallowRef<Editor>()
const errorMsg = ref('')
const zoom = ref(100)

const refrescar = () => { try { editor.value?.refresh() } catch { /* noop */ } }
const onFullscreen = () => { setTimeout(refrescar, 80); setTimeout(() => { refrescar(); ajustarZoom() }, 320) }

const canvasNode = () => el.value?.querySelector('.gjs-cv-canvas') as HTMLElement | null

// El lienzo NO se mueve mientras el correo quepa en pantalla: solo se permite
// scroll cuando de verdad es más alto de lo que se puede mostrar.
function actualizarScroll() {
  const ed = editor.value
  const canvasEl = canvasNode()
  const doc = ed?.Canvas.getDocument()
  const body = ed?.Canvas.getBody()
  if (!canvasEl || !doc || !body) return
  const altoContenido = body.scrollHeight * (zoom.value / 100)
  const modo = altoContenido - 4 > canvasEl.clientHeight ? 'auto' : 'hidden'
  canvasEl.style.overflow = modo
  doc.documentElement.style.overflowY = modo
  body.style.overflowY = modo
}

// Zoom SOLO del lienzo (la parte blanca del correo); los paneles/opciones no cambian.
function aplicarZoom(v: number) {
  const z = Math.round(Math.max(25, Math.min(200, v)))
  zoom.value = z
  try { editor.value?.Canvas.setZoom(z) } catch { /* noop */ }
  setTimeout(actualizarScroll, 30)
}
const zoomIn = () => aplicarZoom(zoom.value + 10)
const zoomOut = () => aplicarZoom(zoom.value - 10)
const zoomReset = () => aplicarZoom(100)
function ajustarZoom() {
  const ed = editor.value
  const canvasEl = canvasNode()
  const body = ed?.Canvas.getBody()
  if (!ed || !canvasEl || !body) return
  const contentH = body.scrollHeight || 1
  const contentW = body.scrollWidth || 1
  const dispoH = canvasEl.clientHeight - 24
  const dispoW = canvasEl.clientWidth - 24
  aplicarZoom(Math.min(100, (dispoH / contentH) * 100, (dispoW / contentW) * 100))
}

let tFit: ReturnType<typeof setTimeout> | undefined
const reajustar = () => { clearTimeout(tFit); tFit = setTimeout(() => { ajustarZoom() }, 180) }
const onResize = () => { refrescar(); reajustar() }

onMounted(async () => {
  await nextTick()
  if (!el.value) return
  try {
    const ed = grapesjs.init({
      container: el.value,
      height: '100%',
      fromElement: false,
      storageManager: false,
      protectedCss: '',
      assetManager: { embedAsBase64: true },
      // Estilos SOLO del lienzo del editor (no se exportan): dan a la vista el
      // aspecto de un editor de correo — el correo "flota" centrado sobre gris.
      canvas: {
        styles: [
          'data:text/css,' + encodeURIComponent(
            'html,body{overflow-x:hidden}'
            + 'body>*:first-child{box-shadow:0 2px 8px rgba(15,23,42,.08),0 14px 40px rgba(15,23,42,.07)}',
          ),
        ],
      },
      blockManager: { blocks: BLOQUES_CORREO, appendOnClick: true },
      selectorManager: { componentFirst: true },
      // Un solo tamaño por ahora: el ancho de correo (680 px), sin selector.
      // widthMedia: '' a proposito -> sin esto, GrapesJS trata cualquier
      // dispositivo con `width` como un breakpoint responsive y envuelve
      // TODO cambio de estilo en `@media (max-width: 680px){...}`. Como aca
      // solo hay un tamaño fijo (no es responsive de verdad), eso hacia que
      // los cambios de color/estilo quedaran en un <style> aparte que
      // inlinearCss no mete inline, y en muchos clientes de correo (o al
      // abrir el .html en una ventana normal, mas ancha que 680px) esa regla
      // nunca se aplicaba: se veia el color original de la plantilla, como
      // si el cambio no se hubiera guardado.
      deviceManager: {
        default: 'correo',
        devices: [{ id: 'correo', name: 'Correo', width: '680px', widthMedia: '' }],
      },
      styleManager: { sectors: SECTORES_ESTILO },
    })
    editor.value = ed

    // Limpieza de la barra propia de GrapesJS: fuera el selector de dispositivo,
    // el toggle de contornos (el "hover" de los bloques), la vista de código
    // nativa y la vista previa (el ojo).
    try { ed.Panels.removeButton('options', 'sw-visibility') } catch { /* noop */ }
    try { ed.Panels.removeButton('options', 'export-template') } catch { /* noop */ }
    try { ed.Panels.removeButton('options', 'preview') } catch { /* noop */ }
    try { ed.Panels.removePanel('devices-c') } catch { /* noop */ }

    ed.on('load', () => {
      refrescar()
      // El correo "flota" sobre un lienzo gris claro (como los editores de
      // correo). Sin min-height: solo aparece scroll si el correo NO cabe en la
      // pantalla; si cabe, no hay barra. Es solo presentación del editor, no se
      // guarda en la plantilla.
      const doc = ed.Canvas.getDocument()
      if (doc?.documentElement) doc.documentElement.style.background = '#e9edf4'
      const body = ed.Canvas.getBody()
      if (body) {
        body.style.background = '#e9edf4'
        body.style.margin = '0'
        body.style.padding = '20px 0'
      }
      // Arranca ajustado para que el correo completo entre en pantalla.
      setTimeout(ajustarZoom, 120)
    })
    // Cuando cambia el contenido (agregar/quitar/mover/editar bloques) se
    // reajusta el zoom para que el correo siga cabiendo sin necesidad de scroll.
    // component:styleUpdate (cambiar color/fondo/etc desde el panel de estilos)
    // se agrega aparte: sin este evento el lienzo no se repinta al cambiar
    // solo un estilo (el dato SÍ queda actualizado -> se ve bien al exportar/
    // descargar, pero visualmente en el editor parecía que "no pegó" el
    // cambio hasta hacer otra accion).
    ed.on(
      'component:add component:remove component:update:components canvas:drop component:styleUpdate',
      reajustar,
    )
    window.addEventListener('resize', onResize)
    document.addEventListener('fullscreenchange', onFullscreen)

    cargar(props.plantilla)
    requestAnimationFrame(refrescar)
    setTimeout(refrescar, 150)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : String(e)
    console.error('[EditorHtmlGrapes] init falló:', e)
  }
})

onBeforeUnmount(() => {
  clearTimeout(tFit)
  window.removeEventListener('resize', onResize)
  document.removeEventListener('fullscreenchange', onFullscreen)
  try { editor.value?.destroy() } catch { /* noop */ }
  editor.value = undefined
})

// Este editor tiene un solo tamaño de correo (dispositivo "correo", sin
// widthMedia): nunca debería haber reglas con media query. Plantillas
// guardadas ANTES de ese ajuste sí pueden traer alguna atrapada en
// `@media (max-width: 680px)` dentro de su `proyecto` -> como el lienzo del
// editor mide justo eso, la condición siempre se cumple ahí y esa regla
// vieja le gana visualmente a la nueva aunque el panel de estilos ya
// muestre el valor correcto. Se limpian al cargar para que no vuelvan a
// aparecer.
function limpiarReglasResponsive() {
  const ed = editor.value
  if (!ed) return
  const conMedia = ed.Css.getAll().filter((r) => !!r.get('mediaText'))
  conMedia.forEach((r) => ed.Css.remove(r))
}

function cargar(p: Plantilla | null) {
  const ed = editor.value
  if (!ed) return
  if (p?.proyecto) {
    try {
      ed.loadProjectData(p.proyecto as Parameters<Editor['loadProjectData']>[0])
      limpiarReglasResponsive()
      return
    } catch { /* proyecto corrupto: cae al documento HTML */ }
  }
  setDocumento(p?.html || PLANTILLA_HTML_INICIAL)
}

// ── API expuesta al diálogo ─────────────────────────────────────────
function getHtml(): string { return editor.value?.getHtml() ?? '' }
function getCss(): string { return editor.value?.getCss() ?? '' }
function getProjectData(): unknown { return editor.value?.getProjectData() ?? null }
/** Documento de correo en UN solo archivo HTML, con los estilos inline. */
function getDocumento(asunto = 'Correo'): string {
  const ed = editor.value
  if (!ed) return ''
  // OJO: sin `cleanId`. GrapesJS guarda cada cambio de estilo (color, fondo,
  // fuente…) como una regla CSS con selector `#id-autogenerado`; `cleanId`
  // borra justo esos ids del HTML, así que luego `inlinearCss` no encuentra
  // el elemento y el estilo nuevo se pierde en el HTML que se guarda/envía
  // (por eso "si borro texto sí funciona" pero los estilos no: borrar texto
  // no depende de un id que se pueda perder).
  return armarDocumentoCorreo(ed.getHtml() ?? '', ed.getCss() ?? '', asunto)
}
/** Carga un documento HTML completo (importar plantilla o editar el código):
 *  separa el <style> del <head> y el contenido del <body>. */
function setDocumento(doc: string) {
  const ed = editor.value
  if (!ed) return
  const estilos = [...doc.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/gi)].map(m => m[1].trim()).join('\n\n')
  const bodyMatch = doc.match(/<body[^>]*>([\s\S]*?)<\/body>/i)
  let cuerpo = bodyMatch ? bodyMatch[1] : doc
  cuerpo = cuerpo
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .trim()
  ed.setComponents(cuerpo)
  ed.setStyle(estilos)
  setTimeout(refrescar, 60)
}
function vistaPrevia() { editor.value?.runCommand('preview') }

defineExpose({ cargar, getHtml, getCss, getProjectData, getDocumento, setDocumento, vistaPrevia, ajustarZoom })
</script>

<template>
  <div class="gjs-wrap">
    <div v-if="errorMsg" class="gjs-error">
      No se pudo cargar el editor visual.<br><code>{{ errorMsg }}</code>
    </div>
    <div ref="el" class="gjs-host"></div>

    <!-- Zoom SOLO del lienzo del correo -->
    <div v-if="!errorMsg" class="zoom-pill">
      <button type="button" title="Alejar" @click="zoomOut">&minus;</button>
      <button type="button" title="Zoom 100%" class="zoom-val" @click="zoomReset">{{ zoom }}%</button>
      <button type="button" title="Acercar" @click="zoomIn">+</button>
      <span class="zoom-sep"></span>
      <button type="button" title="Ajustar a la pantalla" @click="ajustarZoom">Ajustar</button>
    </div>
  </div>
</template>

<style>
/* El host necesita tamaño concreto (absolute/inset-0), no un height:100% encadenado. */
.gjs-wrap { position: absolute; inset: 0; }
.gjs-host { position: absolute; inset: 0; }
.gjs-error {
  position: absolute; inset: 0; z-index: 5;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; padding: 24px; text-align: center;
  font: 12px/1.5 Inter, system-ui, sans-serif; color: #b91c1c; background: #fff;
}
.gjs-error code { font-size: 11px; color: #64748b; }

.gjs-host .gjs-editor { font-family: Inter, system-ui, sans-serif; height: 100% !important; }
/* El lienzo no se mueve por defecto; el JS pone overflow:auto solo si el
   correo no cabe en pantalla. */
.gjs-host .gjs-cv-canvas { background-color: #e9edf4 !important; overflow: hidden; }
.gjs-host .gjs-block { border-radius: 6px; }
/* Sin selector de dispositivo (un solo tamaño de correo por ahora). */
.gjs-host .gjs-pn-devices-c { display: none !important; }

/* Pastilla de zoom flotante sobre el lienzo (abajo a la izquierda) */
.zoom-pill {
  position: absolute; left: 12px; bottom: 12px; z-index: 4;
  display: flex; align-items: center; gap: 2px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 9px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, .14); padding: 3px;
  font: 600 11px/1 Inter, system-ui, sans-serif;
}
.zoom-pill button {
  border: 0; background: none; color: #334155; cursor: pointer;
  height: 24px; min-width: 24px; padding: 0 6px; border-radius: 6px;
}
.zoom-pill button:hover { background: #f1f5f9; color: #2447f9; }
.zoom-pill .zoom-val { min-width: 42px; font-variant-numeric: tabular-nums; }
.zoom-pill .zoom-sep { width: 1px; height: 16px; background: #e2e8f0; margin: 0 2px; }
</style>
