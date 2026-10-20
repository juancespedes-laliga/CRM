<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  RefreshCw, FileSpreadsheet, Search, Loader2, Users, Send, MailX, MailOpen, MousePointerClick, UserMinus,
  Check, Minus, CalendarClock, UserRound, ListChecks, AtSign, X,
} from 'lucide-vue-next'
import type { DestinatarioCampanaMT, DetalleCampanaMT } from '../types/mailerturbo'
import { getDestinatariosCampana, getDetalleCampana } from '../services/mailerturbo.api'
import {
  FILTROS_DESTINATARIOS, exportarDestinatariosExcel, fueEnviado, motivoNoEnviado, type FiltroDestinatarios,
} from '../utils/destinatarios'
import CampanasSubnav from '@/features/campanas/components/CampanasSubnav.vue'
import MigasCampanas from '@/features/campanas/components/MigasCampanas.vue'
import Paginador from '../components/Paginador.vue'
import EmbudoCampana from '../components/graficos/EmbudoCampana.vue'
import ResultadoEntrega from '../components/graficos/ResultadoEntrega.vue'
import AperturasTiempo from '../components/graficos/AperturasTiempo.vue'
import BarrasHorizontales from '../components/graficos/BarrasHorizontales.vue'

const route = useRoute()
const router = useRouter()
const idCampana = computed(() => Number(route.params.id))
const nf = new Intl.NumberFormat('es-CO')

// ── Carga ────────────────────────────────────────────────────────────
const campana = ref<DetalleCampanaMT | null>(null)
const destinatarios = ref<DestinatarioCampanaMT[]>([])
const cargandoDetalle = ref(false)
const cargandoDestinatarios = ref(false)
const errorDetalle = ref<string | null>(null)
const errorDestinatarios = ref<string | null>(null)

const actualizadoEn = ref<Date | null>(null)
// Refresco sin esqueletos de carga (botón "Actualizar" con datos ya cargados y
// refresco automático): la vista no parpadea, solo gira el ícono del botón.
const refrescando = ref(false)

async function cargar(silencioso = false) {
  const id = idCampana.value
  if (silencioso) refrescando.value = true
  else { cargandoDetalle.value = true; cargandoDestinatarios.value = true }
  errorDetalle.value = null
  errorDestinatarios.value = null
  // El detalle es rápido; los destinatarios pueden tardar con campañas grandes.
  const pDetalle = getDetalleCampana(id)
    .then(c => { campana.value = c })
    .catch(e => { errorDetalle.value = e instanceof Error ? e.message : 'No se pudo cargar la campaña.' })
    .finally(() => { cargandoDetalle.value = false })
  try {
    destinatarios.value = await getDestinatariosCampana(id)
  } catch (e) {
    errorDestinatarios.value = e instanceof Error ? e.message : 'No se pudieron cargar los destinatarios.'
  } finally {
    cargandoDestinatarios.value = false
  }
  await pDetalle
  refrescando.value = false
  actualizadoEn.value = new Date()
}
onMounted(() => cargar())
watch(idCampana, () => { pagina.value = 1; void cargar() })
const actualizar = () => cargar(!!campana.value)

// Mientras la campaña se esté enviando (o tenga destinatarios pendientes) se
// refresca sola cada 30 s.
const enCurso = computed(() =>
  ['En proceso', 'Enviando'].includes(campana.value?.estado ?? '')
  || destinatarios.value.some(d => d.estadoEnvio === 'Pendiente'),
)
const ocupado = computed(() => cargandoDetalle.value || cargandoDestinatarios.value || refrescando.value)
const autoRefresco = setInterval(() => { if (enCurso.value && !ocupado.value) void cargar(true) }, 30_000)
onUnmounted(() => clearInterval(autoRefresco))
const fmtHora = (d: Date) => d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

// ── Métricas (desde los destinatarios; si aún no cargan, desde las estadísticas) ──
const conteos = computed(() => {
  const ds = destinatarios.value
  const e = campana.value?.estadisticas
  if (!ds.length && e) {
    const noEnv = e.totalRebotes + e.totalRechazados
    return {
      total: e.totalEnvios, enviados: Math.max(0, e.totalEnvios - noEnv), noEnviados: noEnv, rebotes: e.totalRebotes,
      otrosNoEnviados: e.totalRechazados, abrieron: e.totalVistas, clic: e.totalClicks, bajas: e.totalSalidas, noAbrieron: 0,
    }
  }
  let enviados = 0, rebotes = 0, abrieron = 0, clic = 0, bajas = 0, noAbrieron = 0
  for (const d of ds) {
    const env = fueEnviado(d)
    if (env) { enviados++; if (!d.abrio) noAbrieron++ }
    else if (d.resultadoEnvio.toLowerCase() === 'rebote') rebotes++
    if (d.abrio) abrieron++
    if (d.clic) clic++
    if (d.baja) bajas++
  }
  return {
    total: ds.length, enviados, noEnviados: ds.length - enviados, rebotes,
    otrosNoEnviados: ds.length - enviados - rebotes, abrieron, clic, bajas, noAbrieron,
  }
})

const pct = (n: number, de: number) => (de ? `${((n / de) * 100).toLocaleString('es-CO', { maximumFractionDigits: 1 })}%` : '—')

const kpis = computed(() => {
  const c = conteos.value
  return [
    { id: 'todos' as const, label: 'Destinatarios', valor: c.total, sub: 'en la campaña', icono: Users },
    { id: 'enviados' as const, label: 'Enviados', valor: c.enviados, sub: `${pct(c.enviados, c.total)} entregados`, icono: Send },
    { id: 'no_enviados' as const, label: 'No enviados', valor: c.noEnviados, sub: `${pct(c.noEnviados, c.total)} · rebotes y otros`, icono: MailX },
    { id: 'abrieron' as const, label: 'Abrieron', valor: c.abrieron, sub: `${pct(c.abrieron, c.enviados)} de los enviados`, icono: MailOpen },
    { id: 'clic' as const, label: 'Hicieron clic', valor: c.clic, sub: `${pct(c.clic, c.abrieron)} de los que abrieron`, icono: MousePointerClick },
    { id: 'bajas' as const, label: 'Bajas', valor: c.bajas, sub: `${pct(c.bajas, c.enviados)} de los enviados`, icono: UserMinus },
  ]
})

const etapasEmbudo = computed(() => [
  { id: 'todos', label: 'Destinatarios', valor: conteos.value.total },
  { id: 'enviados', label: 'Entregados', valor: conteos.value.enviados },
  { id: 'abrieron', label: 'Abrieron', valor: conteos.value.abrieron },
  { id: 'clic', label: 'Hicieron clic', valor: conteos.value.clic },
])

const inicioEnvio = computed(() => {
  let min: string | null = null
  for (const d of destinatarios.value) if (d.fechaEnviado && (!min || d.fechaEnviado < min)) min = d.fechaEnviado
  return min ?? campana.value?.fecha ?? null
})
const fechasApertura = computed(() => destinatarios.value.flatMap(d => (d.fechaApertura ? [d.fechaApertura] : [])))
const fechasClic = computed(() => destinatarios.value.flatMap(d => (d.fechaClic ? [d.fechaClic] : [])))

// Migas: el detalle cuelga de la vista desde la que se abrió.
const desdeEstadisticas = computed(() => route.query.desde === 'estadisticas')
const migas = computed(() => [
  desdeEstadisticas.value
    ? { label: 'Estadísticas', ruta: '/campanas/estadisticas' }
    : { label: 'Listas y campañas', ruta: '/campanas/mailerturbo' },
  { label: campana.value?.nombre || `Campaña #${idCampana.value}` },
])

const topLinks = computed(() => {
  const m = new Map<string, number>()
  for (const d of destinatarios.value) for (const l of d.links) m.set(l, (m.get(l) ?? 0) + 1)
  return [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([link, n]) => {
    let label = link
    try { const u = new URL(link); label = (u.pathname.replace(/\/$/, '') || u.hostname) } catch { /* link tal cual */ }
    return { id: link, label, sub: link, valor: n, detalle: `${nf.format(n)} personas hicieron clic` }
  })
})

// ── Tabla ────────────────────────────────────────────────────────────
const filtro = ref<FiltroDestinatarios>((route.query.filtro as FiltroDestinatarios) || 'todos')
const busqueda = ref('')
const pagina = ref(1)
const porPagina = ref(25)

const conteoPorFiltro = computed(() => {
  const r = {} as Record<FiltroDestinatarios, number>
  for (const f of FILTROS_DESTINATARIOS) r[f.id] = 0
  for (const d of destinatarios.value) for (const f of FILTROS_DESTINATARIOS) if (f.cumple(d)) r[f.id]++
  return r
})

const filtrados = computed(() => {
  const f = FILTROS_DESTINATARIOS.find(x => x.id === filtro.value) ?? FILTROS_DESTINATARIOS[0]
  const q = busqueda.value.trim().toLowerCase()
  return destinatarios.value.filter(d =>
    f.cumple(d) && (!q || d.correo.toLowerCase().includes(q) || d.nombre.toLowerCase().includes(q) || (d.telefono ?? '').includes(q)),
  )
})
const totalPaginas = computed(() => Math.max(1, Math.ceil(filtrados.value.length / porPagina.value)))
const visibles = computed(() => filtrados.value.slice((pagina.value - 1) * porPagina.value, pagina.value * porPagina.value))
watch([filtro, busqueda, porPagina], () => { pagina.value = 1 })
watch(filtro, f => { void router.replace({ query: { ...route.query, filtro: f === 'todos' ? undefined : f } }) })

const tablaRef = ref<HTMLElement | null>(null)
function verFiltro(id: string) {
  filtro.value = id as FiltroDestinatarios
  tablaRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ── Exportar ─────────────────────────────────────────────────────────
const etiquetaFiltro = computed(() => FILTROS_DESTINATARIOS.find(f => f.id === filtro.value)?.label ?? 'Todos')
function exportarTodo() {
  if (campana.value) exportarDestinatariosExcel(campana.value, destinatarios.value)
}
function exportarVista() {
  if (campana.value) exportarDestinatariosExcel(campana.value, destinatarios.value, { label: etiquetaFiltro.value, filas: filtrados.value })
}

// ── Formato ──────────────────────────────────────────────────────────
const COLOR_ESTADO: Record<string, string> = {
  Enviada: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
  Enviando: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
  'En proceso': 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
  'En espera': 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300',
  Programada: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300',
  Borrador: 'bg-slate-100 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300',
}
const claseEstado = (estado: string) => COLOR_ESTADO[estado] ?? COLOR_ESTADO.Borrador
const fmtFecha = (f: string | null) => (f ? new Date(f.replace(' ', 'T')).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' }) : '—')
const fmtCorta = (f: string | null) => (f ? new Date(f.replace(' ', 'T')).toLocaleString('es-CO', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '')
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <CampanasSubnav />

    <!-- Encabezado -->
    <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
      <div class="min-w-0">
        <MigasCampanas :migas="migas" class="mb-2" />
        <div v-if="cargandoDetalle && !campana" class="h-6 w-64 rounded bg-slate-100 dark:bg-slate-700 animate-pulse" />
        <template v-else-if="campana">
          <div class="flex flex-wrap items-center gap-2">
            <h2 class="text-[18px] font-bold text-heading truncate" :title="campana.nombre">{{ campana.nombre }}</h2>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-md" :class="claseEstado(campana.estado)">{{ campana.estado }}</span>
            <span class="text-[10px] text-subtle">#{{ campana.id }}</span>
          </div>
          <p class="text-[12px] text-body mt-0.5">{{ campana.asunto || 'Sin asunto' }}</p>
          <div class="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[11px] text-muted">
            <span class="flex items-center gap-1"><CalendarClock :size="12" /> {{ fmtFecha(campana.fecha || campana.fechaProgramacion) }}</span>
            <span v-if="campana.perfilEnvio" class="flex items-center gap-1" :title="campana.correoPerfilEnvio || ''"><AtSign :size="12" /> {{ campana.perfilEnvio }}</span>
            <span v-if="campana.listas" class="flex items-center gap-1"><ListChecks :size="12" /> {{ campana.listas }}</span>
            <span v-if="campana.usuarioEnvio" class="flex items-center gap-1"><UserRound :size="12" /> {{ campana.usuarioEnvio }}</span>
          </div>
        </template>
        <p v-if="errorDetalle" class="text-[12px] text-red-600 dark:text-red-400 mt-1">{{ errorDetalle }}</p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <span v-if="actualizadoEn" class="text-[10px] text-subtle text-right leading-tight">
          Actualizado {{ fmtHora(actualizadoEn) }}<template v-if="enCurso"><br>se actualiza sola cada 30 s</template>
        </span>
        <button
          @click="actualizar"
          :disabled="ocupado"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
        ><RefreshCw :size="13" :class="{ 'animate-spin': ocupado }" /> Actualizar</button>
        <button
          @click="exportarTodo"
          :disabled="!campana || cargandoDestinatarios || !destinatarios.length"
          class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-emerald-600 text-white text-[11px] font-bold shadow hover:bg-emerald-700 disabled:opacity-50"
          title="Excel con hojas: Resumen, Enviados, No enviados y Todos"
        ><FileSpreadsheet :size="13" /> Exportar Excel</button>
      </div>
    </div>

    <!-- KPIs (clic = filtrar la tabla) -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
      <button
        v-for="k in kpis"
        :key="k.id"
        type="button"
        class="surface-card rounded-2xl shadow-sm px-4 py-3 text-left transition-all hover:shadow-md hover:-translate-y-px"
        :class="{ 'ring-2 ring-[#2447F9]/60': filtro === k.id && !cargandoDestinatarios }"
        @click="verFiltro(k.id)"
      >
        <div class="flex items-center gap-1.5 text-[11px] font-semibold text-muted"><component :is="k.icono" :size="13" /> {{ k.label }}</div>
        <div class="text-[22px] font-bold text-heading tabular-nums leading-tight mt-1">
          <span v-if="cargandoDetalle && cargandoDestinatarios" class="inline-block h-6 w-16 rounded bg-slate-100 dark:bg-slate-700 animate-pulse" />
          <template v-else>{{ nf.format(k.valor) }}</template>
        </div>
        <div class="text-[10px] text-muted truncate">{{ k.sub }}</div>
      </button>
    </div>

    <!-- Gráficas -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <section class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">Embudo de la campaña</h3>
        <p class="text-[11px] text-muted mb-3">Cuántos llegan a cada etapa, sobre el total de destinatarios.</p>
        <EmbudoCampana :etapas="etapasEmbudo" @seleccionar="verFiltro" />
      </section>
      <section class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">Resultado de la entrega</h3>
        <p class="text-[11px] text-muted mb-4">A quiénes sí les llegó el correo y a quiénes no.</p>
        <ResultadoEntrega :entregados="conteos.enviados" :rebotes="conteos.rebotes" :otros-no-enviados="conteos.otrosNoEnviados" @seleccionar="verFiltro" />
      </section>
      <section class="surface-card rounded-2xl shadow-sm p-4" :class="{ 'xl:col-span-2': !topLinks.length }">
        <h3 class="text-[13px] font-bold text-heading">Aperturas en el tiempo</h3>
        <p class="text-[11px] text-muted mb-2">Cuándo abrieron el correo, desde el inicio del envío.</p>
        <div v-if="cargandoDestinatarios" class="h-48 flex items-center justify-center text-[12px] text-muted"><Loader2 :size="14" class="animate-spin mr-1" /> Cargando…</div>
        <AperturasTiempo v-else :inicio="inicioEnvio" :aperturas="fechasApertura" :clics="fechasClic" />
      </section>
      <section v-if="topLinks.length" class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">Links con más clics</h3>
        <p class="text-[11px] text-muted mb-3">Personas distintas que hicieron clic en cada link.</p>
        <BarrasHorizontales :items="topLinks" />
      </section>
    </div>

    <!-- Destinatarios -->
    <section ref="tablaRef" class="surface-card rounded-2xl shadow-sm overflow-hidden scroll-mt-4">
      <div class="px-4 py-3 border-b border-default flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="text-[13px] font-bold text-heading">Destinatarios</h3>
          <p class="text-[11px] text-muted">A quién se le envió, a quién no, y qué hizo con el correo.</p>
        </div>
        <div class="flex items-center gap-2 w-full sm:w-auto">
          <div class="flex items-center gap-2 h-9 px-3 rounded-lg input-surface flex-1 sm:w-64">
            <Search :size="13" class="text-muted shrink-0" />
            <input v-model="busqueda" placeholder="Buscar nombre, correo o teléfono…" class="flex-1 min-w-0 bg-transparent text-[12px] outline-none text-body" />
            <button v-if="busqueda" type="button" class="text-muted hover:text-heading" title="Limpiar" @click="busqueda = ''"><X :size="12" /></button>
          </div>
          <button
            @click="exportarVista"
            :disabled="!campana || !filtrados.length"
            class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 whitespace-nowrap"
            :title="`Exporta solo las ${nf.format(filtrados.length)} filas de «${etiquetaFiltro}»${busqueda ? ' con la búsqueda' : ''}`"
          ><FileSpreadsheet :size="13" /> Exportar esta vista</button>
        </div>
      </div>

      <div class="px-4 py-2.5 border-b border-default flex gap-1.5 overflow-x-auto" role="tablist">
        <button
          v-for="f in FILTROS_DESTINATARIOS"
          :key="f.id"
          type="button"
          role="tab"
          :aria-selected="filtro === f.id"
          class="flex items-center gap-1.5 h-8 px-3 rounded-full text-[11px] font-semibold whitespace-nowrap border transition-colors"
          :class="filtro === f.id
            ? 'bg-[#2447F9] border-[#2447F9] text-white'
            : 'border-default bg-white dark:bg-slate-800 text-body hover:bg-slate-50 dark:hover:bg-slate-700'"
          @click="filtro = f.id"
        >
          {{ f.label }}
          <span class="tabular-nums text-[10px] px-1.5 rounded-full" :class="filtro === f.id ? 'bg-white/20' : 'bg-slate-100 dark:bg-slate-700 text-muted'">
            {{ cargandoDestinatarios ? '…' : nf.format(conteoPorFiltro[f.id]) }}
          </span>
        </button>
      </div>

      <div v-if="errorDestinatarios" class="px-4 py-3 text-[12px] text-red-600 dark:text-red-400">{{ errorDestinatarios }}</div>

      <div class="overflow-x-auto">
        <table class="w-full text-[12px]">
          <thead>
            <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
              <th class="px-4 py-2.5 font-semibold">Destinatario</th>
              <th class="px-3 py-2.5 font-semibold">Envío</th>
              <th class="px-3 py-2.5 font-semibold">Abrió</th>
              <th class="px-3 py-2.5 font-semibold">Clic</th>
              <th class="px-3 py-2.5 font-semibold">Baja</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="cargandoDestinatarios">
              <td colspan="5" class="px-4 py-10 text-center text-muted"><Loader2 :size="14" class="animate-spin inline mr-1" /> Consultando los destinatarios en MailerTurbo…</td>
            </tr>
            <template v-else>
              <tr v-for="(d, i) in visibles" :key="`${d.correo}-${i}`"class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                <td class="px-4 py-2 min-w-[240px]">
                  <div class="font-semibold text-heading truncate max-w-[340px]" :title="d.nombre">{{ d.nombre || '—' }}</div>
                  <div class="text-[11px] text-muted truncate max-w-[340px]">{{ d.correo }}<template v-if="d.telefono"> · {{ d.telefono }}</template></div>
                </td>
                <td class="px-3 py-2 whitespace-nowrap">
                  <span v-if="fueEnviado(d)" class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                    <Check :size="11" /> Enviado
                  </span>
                  <span v-else class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300">
                    <MailX :size="11" /> {{ motivoNoEnviado(d) }}
                  </span>
                  <div class="text-[10px] text-muted mt-0.5">{{ fmtCorta(d.fechaEnviado) }}</div>
                </td>
                <td class="px-3 py-2 whitespace-nowrap">
                  <span v-if="d.abrio" class="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-300 font-semibold"><MailOpen :size="12" /> Sí</span>
                  <span v-else class="inline-flex items-center gap-1 text-muted"><Minus :size="12" /> No</span>
                  <div v-if="d.fechaApertura" class="text-[10px] text-muted">{{ fmtCorta(d.fechaApertura) }}</div>
                </td>
                <td class="px-3 py-2 whitespace-nowrap" :title="d.links.join('\n')">
                  <span v-if="d.clic" class="inline-flex items-center gap-1 text-[#2447F9] dark:text-blue-300 font-semibold"><MousePointerClick :size="12" /> Sí<template v-if="d.links.length > 1"> ({{ d.links.length }})</template></span>
                  <span v-else class="inline-flex items-center gap-1 text-muted"><Minus :size="12" /> No</span>
                  <div v-if="d.fechaClic" class="text-[10px] text-muted">{{ fmtCorta(d.fechaClic) }}</div>
                </td>
                <td class="px-3 py-2 whitespace-nowrap">
                  <span v-if="d.baja" class="inline-flex items-center gap-1 text-red-600 dark:text-red-400 font-semibold"><UserMinus :size="12" /> Sí</span>
                  <span v-else class="text-muted">—</span>
                  <div v-if="d.fechaBaja" class="text-[10px] text-muted">{{ fmtCorta(d.fechaBaja) }}</div>
                </td>
              </tr>
              <tr v-if="!visibles.length && !errorDestinatarios">
                <td colspan="5" class="px-4 py-10 text-center text-muted">
                  {{ busqueda ? 'Nadie coincide con la búsqueda.' : `No hay destinatarios en «${etiquetaFiltro}».` }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div class="px-4 py-2.5 border-t border-default">
        <Paginador
          v-model:pagina="pagina"
          v-model:por-pagina="porPagina"
          :total-paginas="totalPaginas"
          :total="filtrados.length"
          :deshabilitado="cargandoDestinatarios"
        />
      </div>
    </section>
  </div>
</template>
