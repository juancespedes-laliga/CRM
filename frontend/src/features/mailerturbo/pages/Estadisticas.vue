<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { BarChart3, RefreshCw, Loader2, Mails, MailOpen, MousePointerClick, TriangleAlert, ChevronRight } from 'lucide-vue-next'
import type { CampanaMT } from '../types/mailerturbo'
import { getCampanas } from '../services/mailerturbo.api'
import CampanasSubnav from '@/features/campanas/components/CampanasSubnav.vue'
import MigasCampanas from '@/features/campanas/components/MigasCampanas.vue'
import Paginador from '../components/Paginador.vue'
import GraficoLineas, { type CategoriaLineas } from '../components/graficos/GraficoLineas.vue'

// Estadísticas de las campañas de MailerTurbo: tendencias por campaña o por mes.
// ListarCampanas trae los totales de cada campaña; se piden hasta 200 de una vez.
const router = useRouter()
const nf = new Intl.NumberFormat('es-CO')
const fmtPct = (n: number) => `${Number(n || 0).toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`
const MAX_CAMPANAS = 200

const campanas = ref<CampanaMT[]>([])
const cargando = ref(false)
const error = ref<string | null>(null)
async function cargar() {
  cargando.value = true
  error.value = null
  try {
    campanas.value = (await getCampanas(1, MAX_CAMPANAS)).campanas
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudieron cargar las campañas.'
  } finally {
    cargando.value = false
  }
}
onMounted(cargar)

// ── Filtros ──────────────────────────────────────────────────────────
const PERIODOS = [
  { id: 10, label: 'Últimas 10' },
  { id: 20, label: 'Últimas 20' },
  { id: 0, label: 'Todas' },
] as const
const periodo = ref<number>(10)
const agrupar = ref<'campana' | 'mes'>('campana')

const aFecha = (f: string) => new Date(f.replace(' ', 'T'))
// Enviadas (con envíos y fecha), de la más antigua a la más reciente.
const enviadas = computed(() =>
  campanas.value
    .filter(c => c.totalEnvios > 0 && c.fecha)
    .sort((a, b) => (a.fecha! < b.fecha! ? -1 : 1)),
)
const delPeriodo = computed(() => (periodo.value ? enviadas.value.slice(-periodo.value) : enviadas.value))

// ── KPIs ─────────────────────────────────────────────────────────────
const tasa = (n: number, de: number) => (de ? (n / de) * 100 : 0)
const kpis = computed(() => {
  const cs = delPeriodo.value
  const envios = cs.reduce((s, c) => s + c.totalEnvios, 0)
  const vistas = cs.reduce((s, c) => s + c.totalVistas, 0)
  const clicks = cs.reduce((s, c) => s + c.totalClicks, 0)
  const rebotes = cs.reduce((s, c) => s + c.totalRebotes, 0)
  return [
    { label: 'Correos enviados', valor: nf.format(envios), sub: `en ${nf.format(cs.length)} campañas`, icono: Mails },
    { label: 'Tasa de apertura', valor: fmtPct(tasa(vistas, envios)), sub: `${nf.format(vistas)} aperturas`, icono: MailOpen },
    { label: 'Tasa de clics', valor: fmtPct(tasa(clicks, envios)), sub: `${nf.format(clicks)} clics`, icono: MousePointerClick },
    { label: 'Tasa de rebote', valor: fmtPct(tasa(rebotes, envios)), sub: `${nf.format(rebotes)} rebotes`, icono: TriangleAlert },
  ]
})

// ── Puntos de las gráficas (una campaña o un mes por franja) ─────────
interface Punto { cat: CategoriaLineas; envios: number; vistas: number; clicks: number; rebotes: number }
const puntos = computed<Punto[]>(() => {
  if (agrupar.value === 'campana') {
    return delPeriodo.value.map(c => ({
      cat: {
        id: c.id,
        etiqueta: aFecha(c.fecha!).toLocaleDateString('es-CO', { day: 'numeric', month: 'short' }),
        titulo: c.nombre,
        sub: aFecha(c.fecha!).toLocaleDateString('es-CO', { dateStyle: 'medium' }) + ` · ${nf.format(c.totalEnvios)} enviados`,
      },
      envios: c.totalEnvios, vistas: c.totalVistas, clicks: c.totalClicks, rebotes: c.totalRebotes,
    }))
  }
  const meses = new Map<string, Punto>()
  for (const c of delPeriodo.value) {
    const f = aFecha(c.fecha!)
    const clave = `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, '0')}`
    let p = meses.get(clave)
    if (!p) {
      const etiqueta = f.toLocaleDateString('es-CO', { month: 'short', year: '2-digit' })
      p = { cat: { id: clave, etiqueta, titulo: f.toLocaleDateString('es-CO', { month: 'long', year: 'numeric' }), sub: '' }, envios: 0, vistas: 0, clicks: 0, rebotes: 0 }
      meses.set(clave, p)
    }
    p.envios += c.totalEnvios; p.vistas += c.totalVistas; p.clicks += c.totalClicks; p.rebotes += c.totalRebotes
    p.cat.sub = `${nf.format(p.envios)} enviados`
  }
  return [...meses.values()]
})

const categorias = computed(() => puntos.value.map(p => p.cat))
const seriesTasas = computed(() => [
  { id: 'apertura', nombre: 'Apertura', valores: puntos.value.map(p => tasa(p.vistas, p.envios)) },
  { id: 'clics', nombre: 'Clics', valores: puntos.value.map(p => tasa(p.clicks, p.envios)) },
  { id: 'rebote', nombre: 'Rebote', valores: puntos.value.map(p => tasa(p.rebotes, p.envios)) },
])
const seriesVolumen = computed(() => [
  { id: 'enviados', nombre: 'Enviados', valores: puntos.value.map(p => p.envios) },
  { id: 'aperturas', nombre: 'Aperturas', valores: puntos.value.map(p => p.vistas) },
  { id: 'rebotes', nombre: 'Rebotes', valores: puntos.value.map(p => p.rebotes) },
])

const verCampana = (id: string | number) => router.push({ path: `/campanas/mailerturbo/${id}`, query: { desde: 'estadisticas' } })
const onSeleccionar = (c: CategoriaLineas) => { if (agrupar.value === 'campana') void verCampana(c.id) }

// ── Ranking del periodo ──────────────────────────────────────────────
type Orden = 'apertura' | 'clics' | 'rebote' | 'envios'
const orden = ref<Orden>('apertura')
const ORDENES: Record<Orden, string> = { apertura: 'Apertura', clics: 'Clics', rebote: 'Rebote', envios: 'Enviados' }
const valorOrden = (c: CampanaMT) =>
  orden.value === 'apertura' ? c.porcentajeVistas
    : orden.value === 'clics' ? c.porcentajeClicks
      : orden.value === 'rebote' ? tasa(c.totalRebotes, c.totalEnvios)
        : c.totalEnvios
const ranking = computed(() => [...delPeriodo.value].sort((a, b) => valorOrden(b) - valorOrden(a)))
const POR_PAGINA = 10
const pagina = ref(1)
const totalPaginas = computed(() => Math.max(1, Math.ceil(ranking.value.length / POR_PAGINA)))
const rankingVisible = computed(() => ranking.value.slice((pagina.value - 1) * POR_PAGINA, pagina.value * POR_PAGINA))
watch([orden, periodo], () => { pagina.value = 1 })

const fmtFecha = (f: string | null) => (f ? aFecha(f).toLocaleDateString('es-CO', { dateStyle: 'medium' }) : '—')
const segmentado = 'flex rounded-lg border border-default p-0.5 text-[11px] font-semibold bg-white dark:bg-slate-800'
const opcion = (activa: boolean) => ['h-7 px-2.5 rounded-md transition-colors whitespace-nowrap', activa ? 'bg-[#2447F9] text-white' : 'text-muted hover:text-heading']
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
      <div>
        <MigasCampanas :migas="[{ label: 'Estadísticas' }]" class="mb-1.5" />
        <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
          <BarChart3 :size="19" class="text-[#2447F9]" /> Estadísticas de campañas
        </h2>
        <p class="text-[12px] text-body mt-0.5">Cómo les va a los envíos de MailerTurbo a lo largo del tiempo.</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <div :class="segmentado" role="tablist" aria-label="Periodo">
          <button v-for="p in PERIODOS" :key="p.id" type="button" role="tab" :aria-selected="periodo === p.id" :class="opcion(periodo === p.id)" @click="periodo = p.id">{{ p.label }}</button>
        </div>
        <div :class="segmentado" role="tablist" aria-label="Agrupar">
          <button type="button" role="tab" :aria-selected="agrupar === 'campana'" :class="opcion(agrupar === 'campana')" @click="agrupar = 'campana'">Por campaña</button>
          <button type="button" role="tab" :aria-selected="agrupar === 'mes'" :class="opcion(agrupar === 'mes')" @click="agrupar = 'mes'">Por mes</button>
        </div>
        <button
          @click="cargar"
          :disabled="cargando"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
        ><RefreshCw :size="13" :class="{ 'animate-spin': cargando }" /> Actualizar</button>
      </div>
    </div>

    <CampanasSubnav />

    <p v-if="error" class="text-[12px] text-red-600 dark:text-red-400">{{ error }}</p>

    <!-- KPIs -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div v-for="k in kpis" :key="k.label" class="surface-card rounded-2xl shadow-sm px-4 py-3">
        <div class="flex items-center gap-1.5 text-[11px] font-semibold text-muted"><component :is="k.icono" :size="13" /> {{ k.label }}</div>
        <div class="text-[22px] font-bold text-heading tabular-nums leading-tight mt-1">
          <span v-if="cargando && !campanas.length" class="inline-block h-6 w-16 rounded bg-slate-100 dark:bg-slate-700 animate-pulse" />
          <template v-else>{{ k.valor }}</template>
        </div>
        <div class="text-[10px] text-muted">{{ k.sub }}</div>
      </div>
    </div>

    <!-- Gráficas -->
    <section class="surface-card rounded-2xl shadow-sm p-4">
      <h3 class="text-[13px] font-bold text-heading">Tasas de apertura, clics y rebote</h3>
      <p class="text-[11px] text-muted mb-3">
        Porcentaje sobre los correos enviados{{ agrupar === 'campana' ? ' de cada campaña. Clic en una franja para ver la campaña.' : ' en cada mes.' }}
      </p>
      <div v-if="cargando && !campanas.length" class="h-[260px] flex items-center justify-center text-[12px] text-muted"><Loader2 :size="14" class="animate-spin mr-1" /> Consultando MailerTurbo…</div>
      <GraficoLineas v-else :categorias="categorias" :series="seriesTasas" formato="pct" :clicable="agrupar === 'campana'" @seleccionar="onSeleccionar" />
    </section>

    <section class="surface-card rounded-2xl shadow-sm p-4">
      <h3 class="text-[13px] font-bold text-heading">Volumen de envíos</h3>
      <p class="text-[11px] text-muted mb-3">Correos enviados, aperturas y rebotes{{ agrupar === 'campana' ? ' por campaña' : ' por mes' }}.</p>
      <div v-if="cargando && !campanas.length" class="h-[240px] flex items-center justify-center text-[12px] text-muted"><Loader2 :size="14" class="animate-spin mr-1" /> Consultando MailerTurbo…</div>
      <GraficoLineas v-else :categorias="categorias" :series="seriesVolumen" :alto="240" :clicable="agrupar === 'campana'" @seleccionar="onSeleccionar" />
    </section>

    <!-- Ranking -->
    <section class="surface-card rounded-2xl shadow-sm overflow-hidden">
      <div class="px-4 py-3 border-b border-default flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-[13px] font-bold text-heading">Campañas del periodo</h3>
          <p class="text-[11px] text-muted">Ordenadas por {{ ORDENES[orden].toLowerCase() }}, de mayor a menor.</p>
        </div>
        <div :class="segmentado" role="tablist" aria-label="Ordenar por">
          <button v-for="(label, o) in ORDENES" :key="o" type="button" role="tab" :aria-selected="orden === o" :class="opcion(orden === o)" @click="orden = o">{{ label }}</button>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-[12px]">
          <thead>
            <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
              <th class="px-4 py-2.5 font-semibold w-10">#</th>
              <th class="px-3 py-2.5 font-semibold">Campaña</th>
              <th class="px-3 py-2.5 font-semibold text-right">Enviados</th>
              <th class="px-3 py-2.5 font-semibold text-right">Apertura</th>
              <th class="px-3 py-2.5 font-semibold text-right">Clics</th>
              <th class="px-3 py-2.5 font-semibold text-right">Rebote</th>
              <th class="w-8" />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(c, i) in rankingVisible"
              :key="c.id"
              tabindex="0"
              class="group border-b border-slate-100 dark:border-slate-800 cursor-pointer hover:bg-blue-50/50 dark:hover:bg-slate-700/40 focus-visible:outline-2 focus-visible:outline-[#2447F9]"
              @click="verCampana(c.id)"
              @keydown.enter="verCampana(c.id)"
            >
              <td class="px-4 py-2.5 text-muted tabular-nums">{{ (pagina - 1) * POR_PAGINA + i + 1 }}</td>
              <td class="px-3 py-2.5 min-w-[220px]">
                <div class="font-semibold text-heading truncate max-w-[360px] group-hover:text-[#2447F9]" :title="c.nombre">{{ c.nombre }}</div>
                <div class="text-[10px] text-muted">{{ fmtFecha(c.fecha) }}<template v-if="c.listas"> · {{ c.listas }}</template></div>
              </td>
              <td class="px-3 py-2.5 text-right tabular-nums font-semibold text-heading">{{ nf.format(c.totalEnvios) }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="orden === 'apertura' ? 'font-bold text-heading' : 'text-body'">{{ fmtPct(c.porcentajeVistas) }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="orden === 'clics' ? 'font-bold text-heading' : 'text-body'">{{ fmtPct(c.porcentajeClicks) }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums" :class="orden === 'rebote' ? 'font-bold text-heading' : 'text-body'">{{ fmtPct(tasa(c.totalRebotes, c.totalEnvios)) }}</td>
              <td class="pr-3 py-2.5 text-muted group-hover:text-[#2447F9]"><ChevronRight :size="15" /></td>
            </tr>
            <tr v-if="!ranking.length && !cargando">
              <td colspan="7" class="px-4 py-10 text-center text-muted">No hay campañas enviadas.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-2.5 border-t border-default">
        <Paginador v-model:pagina="pagina" :total-paginas="totalPaginas" :total="ranking.length" :por-pagina="POR_PAGINA" :opciones-por-pagina="[]" />
      </div>
    </section>
  </div>
</template>
