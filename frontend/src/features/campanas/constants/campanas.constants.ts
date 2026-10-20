import type { Plantilla, PlantillaDraft } from '../types/plantilla'

// ── Plantillas HTML (editor visual) ───────────────────────────────────
// Persistencia solo en el navegador por ahora (localStorage), ver services/plantillas.api.ts.
export const PLANTILLAS_STORAGE_KEY = 'crm-campanas-plantillas'
export const GRUPOS_STORAGE_KEY = 'crm-campanas-grupos-correo'
// ids de plantillas "seed-…" que ya se "promovieron" a una fila real en el
// backend (ver actualizarPlantilla en services/plantillas.api.ts): dejan de
// re-sembrarse desde PLANTILLAS_MOCK para no aparecer duplicadas.
export const PLANTILLAS_PROMOVIDAS_STORAGE_KEY = 'crm-campanas-plantillas-promovidas'

export const PLANTILLA_DRAFT_VACIO: PlantillaDraft = {
  nombre: '', asunto: '', html: '', css: '', proyecto: null,
}

// HTML de arranque cuando se crea una plantilla nueva (tablas + estilos inline,
// como pide el correo). El editor la carga y el usuario la modifica visualmente.
export const PLANTILLA_HTML_INICIAL = `<table style="width:100%;background:#f4f2eb;padding:24px 0;font-family:Arial,Helvetica,sans-serif" cellpadding="0" cellspacing="0">
  <tr><td align="center">
    <table style="width:600px;max-width:600px;background:#ffffff;border-radius:6px;overflow:hidden" cellpadding="0" cellspacing="0">
      <tr><td style="background:#2447F9;padding:20px 28px">
        <span style="color:#ffffff;font-size:18px;font-weight:bold">Fundación La Liga Ama Salvar Vidas</span>
      </td></tr>
      <tr><td style="padding:32px 28px 8px 28px">
        <h1 style="font-size:22px;color:#0F172A;margin:0 0 12px 0">Hola {{nombre}}</h1>
        <p style="font-size:14px;line-height:1.6;color:#334155;margin:0 0 20px 0">
          Querido afiliado, tenemos información importante para ti. Te contamos las
          novedades y beneficios que tenemos disponibles este mes.
        </p>
      </td></tr>
      <tr><td align="center" style="padding:8px 28px 32px 28px">
        <a href="https://laligaamasalvarvidas.co" style="background:#EC4899;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:6px;font-size:14px;font-weight:bold;display:inline-block">
          Más información
        </a>
      </td></tr>
      <tr><td style="background:#f1e2df;padding:16px 28px;font-size:11px;color:#7a5a56">
        Fundación La Liga Ama Salvar Vidas · Pereira, Colombia<br>
        Si no deseas recibir estos correos, escríbenos para darte de baja.
      </td></tr>
    </table>
  </td></tr>
</table>`

export const PLANTILLAS_MOCK: Plantilla[] = [
  {
    id: 'seed-bienvenida',
    nombre: 'Bienvenida — nuevo afiliado',
    asunto: '¡Bienvenido(a) a la Fundación La Liga Ama Salvar Vidas!',
    html: PLANTILLA_HTML_INICIAL,
    css: '',
    proyecto: null,
    creadoEn: '2026-08-01',
    actualizadoEn: '2026-08-01',
  },
]

export const fmtFechaPlantilla = (iso: string) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

// Descarga el HTML como archivo .html en el navegador.
export const descargarHtml = (nombre: string, html: string) => {
  const slug = (nombre || 'plantilla').toLowerCase().normalize('NFD').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${slug || 'plantilla'}.html`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

// Propiedad -> propiedad abreviada equivalente (o viceversa). Al fusionar
// estilos, fijar una debe reemplazar a la otra: si no, un elemento con
// `background:#2447F9` en el HTML base y un cambio del editor a
// `background-color: green` termina con AMBAS declaraciones en el mismo
// `style="…"`. En el navegador (vista previa/editor) se ve bien porque el
// último valor gana, pero varios clientes de correo (Outlook en particular)
// no resuelven igual esa duplicidad y se quedan con el color viejo — el
// usuario ve "no toma en cuenta mis cambios, manda la plantilla base".
const PROPIEDAD_EQUIVALENTE: Record<string, string> = {
  background: 'background-color',
  'background-color': 'background',
}

// Aplica UNA regla (selector + declaraciones) como estilo inline a los
// elementos que matchea dentro de `tpl`. Se funde por propiedad (mapa) en vez
// de concatenar el texto: así cada propiedad queda UNA sola vez en el style
// final, sin depender de que el cliente de correo respete el orden de
// declaraciones duplicadas.
const aplicarReglaInline = (rule: CSSStyleRule, tpl: HTMLTemplateElement) => {
  let els: NodeListOf<HTMLElement>
  try { els = tpl.content.querySelectorAll(rule.selectorText) } catch { return }
  els.forEach((el) => {
    const props = new Map<string, string>()
    const prev = el.getAttribute('style')
    if (prev) {
      for (const decl of prev.split(';')) {
        const i = decl.indexOf(':')
        if (i === -1) continue
        const prop = decl.slice(0, i).trim().toLowerCase()
        const val = decl.slice(i + 1).trim()
        if (prop && val) props.set(prop, val)
      }
    }
    for (let i = 0; i < rule.style.length; i++) {
      const prop = rule.style.item(i)
      const equivalente = PROPIEDAD_EQUIVALENTE[prop]
      if (equivalente) props.delete(equivalente)
      props.set(prop, rule.style.getPropertyValue(prop).trim())
    }
    const styleFinal = [...props.entries()].map(([p, v]) => `${p}: ${v}`).join('; ')
    el.setAttribute('style', styleFinal)
  })
}

// Pasa las reglas del CSS del editor a estilos INLINE en cada elemento del HTML,
// para que la plantilla quede en UN solo HTML autocontenido (que es además lo
// que mejor soportan los clientes de correo).
//
// Este editor tiene un solo tamaño de correo fijo (no es responsive de
// verdad, ver deviceManager en EditorHtmlGrapes.vue), así que las reglas
// dentro de un `@media` (que GrapesJS a veces genera igual, por su propio
// manejo interno de "dispositivo") TAMBIÉN se pasan inline, igual que las
// normales, en vez de dejarlas aparte en un <style>: si no, cualquier cambio
// de estilo que caiga en un @media se ve bien al descargar/abrir en un
// navegador ancho (el media no aplica ahí) pero se pierde en el correo real
// (los clientes de correo no siempre evalúan igual el media, o lo ignoran).
export const inlinearCss = (html: string, css: string): { html: string; restoCss: string } => {
  if (!css.trim()) return { html, restoCss: '' }
  let sheet: CSSStyleSheet
  try {
    sheet = new CSSStyleSheet()
    sheet.replaceSync(css)
  } catch {
    return { html, restoCss: css }
  }
  const tpl = document.createElement('template')
  tpl.innerHTML = html
  const resto: string[] = []
  for (const rule of Array.from(sheet.cssRules)) {
    if (rule instanceof CSSStyleRule) {
      aplicarReglaInline(rule, tpl)
    } else if (rule instanceof CSSMediaRule) {
      for (const anidada of Array.from(rule.cssRules)) {
        if (anidada instanceof CSSStyleRule) aplicarReglaInline(anidada, tpl)
        else resto.push(anidada.cssText)
      }
    } else {
      resto.push(rule.cssText) // @font-face, etc.
    }
  }
  return { html: tpl.innerHTML, restoCss: resto.join('\n') }
}

// Envuelve el HTML del editor en un documento de correo completo y autocontenido.
// Los estilos van inline en el HTML; solo las @media quedan en un <style>.
export const armarDocumentoCorreo = (html: string, css: string, asunto = 'Correo') => {
  const { html: htmlInline, restoCss } = inlinearCss(html, css)
  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${asunto.replace(/</g, '&lt;')}</title>
${restoCss.trim() ? `<style>\n${restoCss}\n</style>` : ''}
</head>
<body style="margin:0;padding:0">
${htmlInline}
</body>
</html>`
}

const RE_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
export const esCorreoValido = (s: string) => RE_EMAIL.test(s.trim())
// Divide un texto libre ("a@x.com, b@y.com\nc@z.com;") en lista de correos.
export const parsearCorreos = (texto: string): string[] =>
  [...new Set(texto.split(/[\s,;]+/).map(s => s.trim()).filter(Boolean))]
