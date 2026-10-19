<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Mails, MailOpen, MousePointerClick, Pointer, TriangleAlert, ArrowUp, ArrowDown, ChevronRight } from 'lucide-vue-next'
import {
  useEstadisticasCampanas, sumar, valor, fraccion, MESES, nombrePeriodo, totalesDe,
  type Granularidad, type Metrica, type Periodo,
} from '../../composables/useEstadisticasCampanas'
import { pruebaProporciones } from '../../utils/estadistica'
import GraficoLineas, { type CategoriaLineas } from '../graficos/GraficoLineas.vue'
import GraficoTorta from '../graficos/GraficoTorta.vue'
import Paginador from '../Paginador.vue'
import AyudaGrafico from './AyudaGrafico.vue'

const router = useRouter()
const { anios, enPeriodo, puntos } = useEstadisticasCampanas()
const nf = new Intl.NumberFormat('es-CO')
const fmtPct = (n: number | null) => (n == null ? '—' : `${n.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`)

// ── Periodo ──────────────────────────────────────────────────────────
const anio = ref(anios.value[0] ?? new Date().getFullYear())
const mes = ref<number | null>(null)
const por = ref<Granularidad>('mes')
watch(anios, a => { if (!a.includes(anio.value)) anio.value = a[0] })
// Año completo: por mes o por campaña. Un mes: por día o por campaña.
watch(mes, m => { if (m === null && por.value === 'dia') por.value = 'mes'; if (m !== null && por.value === 'mes') por.value = 'dia' })
const periodo = computed<Periodo>(() => ({ anio: anio.value, mes: mes.value }))
const periodoAnterior = computed<Periodo>(() => ({ anio: anio.value - 1, mes: mes.value }))

const campanas = computed(() => enPeriodo(periodo.value))
const totales = computed(() => sumar(campanas.value))
const totalesAnt = computed(() => sumar(enPeriodo(periodoAnterior.value)))

// ── KPIs con variación contra el mismo periodo del año anterior ──────
const KPIS: { m: Metrica; icono: unknown }[] = [
  { m: 'envios', icono: Mails },
  { m: 'apertura', icono: MailOpen },
  { m: 'clics', icono: MousePointerClick },
  { m: 'ctor', icono: Pointer },
  { m: 'rebote', icono: TriangleAlert },
]
const ETIQUETAS: Record<Metrica, string> = {
  envios: 'Correos enviados', apertura: 'Tasa de apertura', clics: 'Tasa de clics (CTR)', ctor: 'Clics / aperturas (CTOR)', rebote: 'Tasa de rebote', bajas: 'Tasa de bajas',
}
// En rebote y bajas, subir es malo.
const MALO_SI_SUBE: Metrica[] = ['rebote', 'bajas']
const kpis = computed(() => KPIS.map(({ m, icono }) => {
  const actual = valor(totales.value, m)
  const ant = valor(totalesAnt.value, m)
  let variacion: { texto: string; sube: boolean; bueno: boolean; signif: boolean | null } | null = null
  if (actual != null && ant != null && totalesAnt.value.envios) {
    if (m === 'envios') {
      const d = ant ? ((actual - ant) / ant) * 100 : 0
      variacion = { texto: `${d >= 0 ? '+' : ''}${d.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`, sube: d >= 0, bueno: d >= 0, signif: null }
    } else {
      const a = fraccion(totales.value, m), b = fraccion(totalesAnt.value, m)
      const p = pruebaProporciones(a.x, a.n, b.x, b.n)
      const d = actual - ant
      variacion = {
        texto: `${d >= 0 ? '+' : ''}${d.toLocaleString('es-CO', { maximumFractionDigits: 1 })} pp`,
        sube: d >= 0,
        bueno: MALO_SI_SUBE.includes(m) ? d <= 0 : d >= 0,
        signif: p?.significativa ?? null,
      }
    }
  }
  const sub = m === 'envios' ? `${nf.format(totales.value.campanas)} campañas`
    : m === 'apertura' ? `${nf.format(totales.value.vistas)} aperturas`
      : m === 'clics' || m === 'ctor' ? `${nf.format(totales.value.clicks)} clics`
        : `${nf.format(totales.value.rebotes)} rebotes`
  return { m, icono, label: ETIQUETAS[m], valor: m === 'envios' ? nf.format(actual ?? 0) : fmtPct(actual), sub, variacion }
}))

// ── Series ───────────────────────────────────────────────────────────
const pts = computed(() => puntos(periodo.value, por.value))
const categorias = computed<CategoriaLineas[]>(() => pts.value.map(p => ({
  id: p.id, etiqueta: p.etiqueta, titulo: p.titulo,
  sub: [p.sub, p.totales.envios ? `${nf.format(p.totales.envios)} enviados` : 'sin envíos'].filter(Boolean).join(' · '),
})))
const seriesTasas = computed(() => (['apertura', 'clics', 'rebote'] as Metrica[]).map(m => ({
  id: m, nombre: { apertura: 'Apertura', clics: 'Clics', rebote: 'Rebote' }[m as 'apertura'], valores: pts.value.map(p => valor(p.totales, m)),
})))
const seriesVolumen = computed(() => [
  { id: 'envios', nombre: 'Enviados', valores: pts.value.map(p => p.totales.envios) },
  { id: 'vistas', nombre: 'Aperturas', valores: pts.value.map(p => p.totales.vistas) },
  { id: 'rebotes', nombre: 'Rebotes', valores: pts.value.map(p => p.totales.rebotes) },
])
const verCampana = (id: string | number) => router.push({ path: `/campanas/mailerturbo/${id}`, query: { desde: 'estadisticas' } })
function onSeleccionar(c: CategoriaLineas) {
  if (por.value === 'campana') void verCampana(c.id)
  else if (por.value === 'mes') { mes.value = Number(c.id); por.value = 'dia' }
}

// ── Tortas ───────────────────────────────────────────────────────────
const tortaResultado = computed(() => {
  const t = totales.value
  const clics = Math.min(t.clicks, t.vistas)
  return [
    { id: 'clic', label: 'Abrieron e hicieron clic', valor: clics },
    { id: 'abrio', label: 'Abrieron sin clic', valor: Math.max(0, t.vistas - clics) },
    { id: 'no', label: 'No abrieron', valor: Math.max(0, t.envios - t.vistas - t.rebotes) },
    { id: 'rebote', label: 'Rebotaron', valor: t.rebotes },
  ]
})
const tortaCampanas = computed(() => {
  const orden = [...campanas.value].sort((a, b) => b.totalEnvios - a.totalEnvios)
  const top = orden.slice(0, 5).map(c => ({ id: c.id, label: c.nombre, valor: c.totalEnvios, detalle: c.f.toLocaleDateString('es-CO', { dateStyle: 'medium' }) }))
  const resto = orden.slice(5)
  if (resto.length) top.push({ id: 'otros' as unknown as number, label: `Otras ${resto.length} campañas`, valor: resto.reduce((s, c) => s + c.totalEnvios, 0), detalle: '' })
  return top
})

// ── Ranking ──────────────────────────────────────────────────────────
const orden = ref<Metrica>('apertura')
const ORDENES: Partial<Record<Metrica, string>> = { apertura: 'Apertura', clics: 'Clics', ctor: 'CTOR', rebote: 'Rebote', envios: 'Enviados' }
const ranking = computed(() => [...campanas.value].sort((a, b) => (valor(totalesDe(b), orden.value) ?? -1) - (valor(totalesDe(a), orden.value) ?? -1)))
const POR_PAGINA = 10
const pagina = ref(1)
const totalPaginas = computed(() => Math.max(1, Math.ceil(ranking.value.length / POR_PAGINA)))
const rankingVisible = computed(() => ranking.value.slice((pagina.value - 1) * POR_PAGINA, pagina.value * POR_PAGINA))
watch([orden, periodo], () => { pagina.value = 1 })

const segmentado = 'flex rounded-lg border border-default p-0.5 text-[11px] font-semibold bg-white dark:bg-slate-800'
const opcion = (activa: boolean) => ['h-7 px-2.5 rounded-md transition-colors whitespace-nowrap disabled:opacity-40', activa ? 'bg-[#2447F9] text-white' : 'text-muted hover:text-heading']
const select = 'h-9 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[12px] text-body outline-none focus:border-[#2447F9]'
</script>

<template>
  <div class="space-y-4">
    <!-- Periodo -->
    <div class="flex flex-wrap items-center gap-2">
      <select v-model.number="anio" :class="select" aria-label="Año">
        <option v-for="a in anios" :key="a" :value="a">{{ a }}</option>
      </select>
      <select v-model="mes" :class="select" aria-label="Mes">
        <option :value="null">Todo el año</option>
        <option v-for="(m, i) in MESES" :key="m" :value="i">{{ m[0].toUpperCase() + m.slice(1) }}</option>
      </select>
      <div :class="segmentado" role="tablist" aria-label="Ver por">
        <button v-if="mes === null" type="button" :class="opcion(por === 'mes')" @click="por = 'mes'">Por mes</button>
        <button v-else type="button" :class="opcion(por === 'dia')" @click="por = 'dia'">Por día</button>
        <button type="button" :class="opcion(por === 'campana')" @click="por = 'campana'">Por campaña</button>
      </div>
      <span class="text-[11px] text-muted ml-1">Comparado con {{ nombrePeriodo(periodoAnterior) }}</span>
    </div>

    <AyudaGrafico titulo="¿Cómo leer los indicadores?">
      <p>Cada tarjeta resume el periodo elegido. La línea de abajo lo compara con <strong>el mismo periodo del año anterior</strong>.</p>
      <ul>
        <li><strong>Verde</strong> = mejoró, <strong>rojo</strong> = empeoró. En rebote, subir es malo, así que se pinta en rojo.</li>
        <li><strong>pp</strong> = puntos porcentuales: de 30% a 33% son +3 pp.</li>
        <li><strong>"significativo"</strong> = el cambio es real. <strong>"no signif."</strong> = puede ser casualidad; no tome decisiones solo con eso.</li>
        <li><strong>CTR</strong>: de cada 100 correos enviados, cuántos hicieron clic. <strong>CTOR</strong>: de cada 100 que abrieron, cuántos hicieron clic (mide qué tan atractivo es el contenido).</li>
      </ul>
    </AyudaGrafico>

    <!-- KPIs -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
      <div v-for="k in kpis" :key="k.m" class="surface-card rounded-2xl shadow-sm px-4 py-3">
        <div class="flex items-center gap-1.5 text-[11px] font-semibold text-muted"><component :is="k.icono" :size="13" /> {{ k.label }}</div>
        <div class="text-[22px] font-bold text-heading tabular-nums leading-tight mt-1">{{ k.valor }}</div>
        <div class="text-[10px] text-muted">{{ k.sub }}</div>
        <div v-if="k.variacion" class="mt-1.5 flex items-center gap-1 text-[10.5px] font-semibold"
          :class="k.variacion.bueno ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'"
          :title="k.variacion.signif === null ? '' : k.variacion.signif ? 'Diferencia estadísticamente significativa (p < 0,05)' : 'No significativa: puede deberse al azar'">
          <component :is="k.variacion.sube ? ArrowUp : ArrowDown" :size="11" />
          {{ k.variacion.texto }} <span class="font-normal text-muted">vs {{ anio - 1 }}</span>
          <span v-if="k.variacion.signif !== null" class="font-normal text-muted">· {{ k.variacion.signif ? 'significativo' : 'no signif.' }}</span>
        </div>
        <div v-else class="mt-1.5 text-[10.5px] text-muted">Sin datos en {{ anio - 1 }}</div>
      </div>
    </div>

    <p v-if="!campanas.length" class="surface-card rounded-2xl px-4 py-6 text-center text-[12px] text-muted">
      No hay campañas enviadas en {{ nombrePeriodo(periodo) }}.
    </p>

    <template v-else>
      <section class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">Tasas de apertura, clics y rebote · {{ nombrePeriodo(periodo) }}</h3>
        <p class="text-[11px] text-muted mb-3">
          Porcentaje sobre los correos enviados {{ por === 'mes' ? 'en cada mes (clic en un mes para verlo por días)' : por === 'dia' ? 'cada día (según la fecha de envío)' : 'de cada campaña (clic para abrirla)' }}.
          Un hueco en la línea = no hubo envíos.
        </p>
        <AyudaGrafico>
          <p>Muestra cómo evolucionan los resultados en el tiempo, para detectar <strong>tendencias</strong> (¿vamos mejorando?) y <strong>picos</strong> (¿qué campaña o mes salió distinto?).</p>
          <ul>
            <li><strong>Azul (apertura):</strong> qué tanto abren los correos. Depende sobre todo del <strong>asunto</strong> y del remitente.</li>
            <li><strong>Naranja (clics):</strong> qué tanto hacen clic. Depende del <strong>contenido</strong> y del botón.</li>
            <li><strong>Verde (rebote):</strong> correos que no llegaron. Si sube, la base tiene correos malos y hay que depurarla.</li>
            <li>Clic en la leyenda para ocultar o mostrar una línea. Clic en {{ por === 'mes' ? 'un mes para verlo por días' : por === 'campana' ? 'un punto para abrir la campaña' : 'un día' }}.</li>
          </ul>
        </AyudaGrafico>
        <GraficoLineas :categorias="categorias" :series="seriesTasas" formato="pct" clicable @seleccionar="onSeleccionar" />
      </section>

      <section class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">Volumen · {{ nombrePeriodo(periodo) }}</h3>
        <p class="text-[11px] text-muted mb-1">Correos enviados, aperturas y rebotes.</p>
        <AyudaGrafico>
          <p>Cantidades, no porcentajes: cuántos correos salieron, cuántos se abrieron y cuántos rebotaron.</p>
          <ul>
            <li>Sirve para ver <strong>cuánto estamos comunicando</strong> y en qué meses se concentran los envíos.</li>
            <li>Si los enviados suben mucho pero las aperturas no, se está enviando más pero no mejor.</li>
          </ul>
        </AyudaGrafico>
        <GraficoLineas :categorias="categorias" :series="seriesVolumen" :alto="230" clicable @seleccionar="onSeleccionar" />
      </section>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <section class="surface-card rounded-2xl shadow-sm p-4">
          <h3 class="text-[13px] font-bold text-heading">Qué pasó con los correos</h3>
          <p class="text-[11px] text-muted mb-3">Reparto de los {{ nf.format(totales.envios) }} correos enviados en {{ nombrePeriodo(periodo) }}.</p>
          <AyudaGrafico>
            <p>Cada porción es una parte del total de correos enviados. Es la foto completa del recorrido del correo:</p>
            <ul>
              <li><strong>Abrieron e hicieron clic:</strong> el mejor resultado, llegaron hasta la acción.</li>
              <li><strong>Abrieron sin clic:</strong> les interesó el asunto pero no el contenido o el botón.</li>
              <li><strong>No abrieron:</strong> el correo llegó, pero el asunto no los convenció (o cayó en promociones/spam).</li>
              <li><strong>Rebotaron:</strong> el correo no existe o no recibe; conviene limpiar esos contactos.</li>
            </ul>
          </AyudaGrafico>
          <GraficoTorta :porciones="tortaResultado" unidad="correos" />
        </section>
        <section class="surface-card rounded-2xl shadow-sm p-4">
          <h3 class="text-[13px] font-bold text-heading">Envíos por campaña</h3>
          <p class="text-[11px] text-muted mb-3">Las 5 campañas con más correos; el resto se agrupa en "Otras".</p>
          <AyudaGrafico>
            <p>Qué campañas se llevaron la mayor parte de los envíos del periodo. Ayuda a saber <strong>dónde se concentró el esfuerzo</strong>: si una sola porción es enorme, los resultados del periodo dependen casi solo de esa campaña.</p>
          </AyudaGrafico>
          <GraficoTorta :porciones="tortaCampanas" unidad="correos" />
        </section>
      </div>

      <section class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-default flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 class="text-[13px] font-bold text-heading">Campañas de {{ nombrePeriodo(periodo) }}</h3>
            <p class="text-[11px] text-muted">Ordenadas por {{ ORDENES[orden]?.toLowerCase() }}, de mayor a menor.</p>
          </div>
          <div :class="segmentado" role="tablist" aria-label="Ordenar por">
            <button v-for="(label, o) in ORDENES" :key="o" type="button" :class="opcion(orden === o)" @click="orden = o">{{ label }}</button>
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
                <th class="px-3 py-2.5 font-semibold text-right">CTOR</th>
                <th class="px-3 py-2.5 font-semibold text-right">Rebote</th>
                <th class="w-8" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="(c, i) in rankingVisible" :key="c.id" tabindex="0"
                class="group border-b border-slate-100 dark:border-slate-800 cursor-pointer hover:bg-blue-50/50 dark:hover:bg-slate-700/40 focus-visible:outline-2 focus-visible:outline-[#2447F9]"
                @click="verCampana(c.id)" @keydown.enter="verCampana(c.id)">
                <td class="px-4 py-2.5 text-muted tabular-nums">{{ (pagina - 1) * POR_PAGINA + i + 1 }}</td>
                <td class="px-3 py-2.5 min-w-[220px]">
                  <div class="font-semibold text-heading truncate max-w-[340px] group-hover:text-[#2447F9]" :title="c.nombre">{{ c.nombre }}</div>
                  <div class="text-[10px] text-muted">{{ c.f.toLocaleDateString('es-CO', { dateStyle: 'medium' }) }}<template v-if="c.listas"> · {{ c.listas }}</template></div>
                </td>
                <td class="px-3 py-2.5 text-right tabular-nums" :class="orden === 'envios' ? 'font-bold text-heading' : 'text-body'">{{ nf.format(c.totalEnvios) }}</td>
                <td v-for="m in (['apertura', 'clics', 'ctor', 'rebote'] as Metrica[])" :key="m" class="px-3 py-2.5 text-right tabular-nums" :class="orden === m ? 'font-bold text-heading' : 'text-body'">{{ fmtPct(valor(totalesDe(c), m)) }}</td>
                <td class="pr-3 py-2.5 text-muted group-hover:text-[#2447F9]"><ChevronRight :size="15" /></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-4 py-2.5 border-t border-default">
          <Paginador v-model:pagina="pagina" :total-paginas="totalPaginas" :total="ranking.length" :por-pagina="POR_PAGINA" :opciones-por-pagina="[]" />
        </div>
      </section>
    </template>
  </div>
</template>
