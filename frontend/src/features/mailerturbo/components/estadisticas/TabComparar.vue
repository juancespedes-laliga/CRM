<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CircleCheck, CircleHelp } from 'lucide-vue-next'
import {
  useEstadisticasCampanas, sumar, valor, fraccion, totalesDe, MESES, MESES_CORTOS, METRICAS, nombrePeriodo, diasDelMes,
  type Metrica, type Totales, type Periodo,
} from '../../composables/useEstadisticasCampanas'
import { pruebaProporciones, textoPrueba, wilson } from '../../utils/estadistica'
import GraficoLineas from '../graficos/GraficoLineas.vue'
import IntervalosConfianza from '../graficos/IntervalosConfianza.vue'
import AyudaGrafico from './AyudaGrafico.vue'

const { anios, validas, enPeriodo } = useEstadisticasCampanas()
const nf = new Intl.NumberFormat('es-CO')
const fmtPct = (n: number | null) => (n == null ? '—' : `${n.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`)
const fmtM = (m: Metrica, v: number | null) => (v == null ? '—' : METRICAS[m].pct ? fmtPct(v) : nf.format(v))

type Modo = 'anios' | 'meses' | 'campanas'
const modo = ref<Modo>('anios')
const metrica = ref<Metrica>('apertura')
const LISTA_METRICAS = Object.keys(METRICAS) as Metrica[]

// ── Tabla A vs B de todas las métricas, con prueba z de dos proporciones ──
function filasComparacion(a: Totales, b: Totales) {
  return LISTA_METRICAS.map(m => {
    const va = valor(a, m), vb = valor(b, m)
    if (m === 'envios') {
      const d = vb ? (((va ?? 0) - vb) / vb) * 100 : null
      return { m, va, vb, delta: d == null ? '—' : `${d >= 0 ? '+' : ''}${d.toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`, prueba: null as ReturnType<typeof pruebaProporciones> }
    }
    const fa = fraccion(a, m), fb = fraccion(b, m)
    const prueba = pruebaProporciones(fa.x, fa.n, fb.x, fb.n)
    return { m, va, vb, delta: prueba ? `${prueba.diferencia >= 0 ? '+' : ''}${prueba.diferencia.toLocaleString('es-CO', { maximumFractionDigits: 1 })} pp` : '—', prueba }
  })
}
const pValor = (p: number) => (p < 0.001 ? '< 0,001' : p.toLocaleString('es-CO', { maximumFractionDigits: 3 }))

// ── Años ─────────────────────────────────────────────────────────────
const anioA = ref(anios.value[0] ?? new Date().getFullYear())
const anioB = ref(anios.value[1] ?? anioA.value - 1)
const totA = computed(() => sumar(enPeriodo({ anio: anioA.value, mes: null })))
const totB = computed(() => sumar(enPeriodo({ anio: anioB.value, mes: null })))
const porMes = (anio: number) => MESES.map((_, i) => sumar(enPeriodo({ anio, mes: i })))
const mesesA = computed(() => porMes(anioA.value))
const mesesB = computed(() => porMes(anioB.value))
const catMeses = MESES.map((m, i) => ({ id: i, etiqueta: MESES_CORTOS[i], titulo: m[0].toUpperCase() + m.slice(1) }))
const seriesAnios = computed(() => [
  { id: `a${anioA.value}`, nombre: String(anioA.value), valores: mesesA.value.map(t => valor(t, metrica.value)) },
  { id: `b${anioB.value}`, nombre: String(anioB.value), valores: mesesB.value.map(t => valor(t, metrica.value)) },
])

// ── Meses ────────────────────────────────────────────────────────────
// Por defecto: el último mes con envíos contra el anterior.
const ultima = validas.value[validas.value.length - 1]
const mesA = ref<Periodo>({ anio: ultima?.anio ?? new Date().getFullYear(), mes: ultima?.mes ?? new Date().getMonth() })
const mesB = ref<Periodo>(mesA.value.mes === 0 ? { anio: mesA.value.anio - 1, mes: 11 } : { anio: mesA.value.anio, mes: (mesA.value.mes ?? 1) - 1 })
const opcionesMes = computed(() => anios.value.flatMap(a => MESES.map((m, i) => ({ valor: `${a}-${i}`, label: `${m[0].toUpperCase() + m.slice(1)} ${a}`, n: enPeriodo({ anio: a, mes: i }).length }))))
const claveMes = (p: Periodo) => `${p.anio}-${p.mes}`
const desdeClave = (k: string): Periodo => { const [a, m] = k.split('-').map(Number); return { anio: a, mes: m } }
const totMesA = computed(() => sumar(enPeriodo(mesA.value)))
const totMesB = computed(() => sumar(enPeriodo(mesB.value)))
const porDia = (p: Periodo) => Array.from({ length: 31 }, (_, i) =>
  i < diasDelMes(p.anio, p.mes ?? 0) ? sumar(enPeriodo(p).filter(c => c.dia === i + 1)) : null)
const catDias = Array.from({ length: 31 }, (_, i) => ({ id: i + 1, etiqueta: String(i + 1), titulo: `Día ${i + 1}` }))
const seriesMeses = computed(() => [
  { id: 'a', nombre: nombrePeriodo(mesA.value), valores: porDia(mesA.value).map(t => (t ? valor(t, metrica.value) : null)) },
  { id: 'b', nombre: nombrePeriodo(mesB.value), valores: porDia(mesB.value).map(t => (t ? valor(t, metrica.value) : null)) },
].map(s => ({ ...s, valores: s.valores.map(v => (metrica.value === 'envios' && v === 0 ? null : v)) })))

// ── Campañas ─────────────────────────────────────────────────────────
const recientes = computed(() => [...validas.value].reverse())
const elegidas = ref<(number | null)[]>([recientes.value[0]?.id ?? null, recientes.value[1]?.id ?? null, null])
watch(recientes, r => { if (!elegidas.value[0] && r[0]) elegidas.value = [r[0].id, r[1]?.id ?? null, null] })
const campanasElegidas = computed(() => elegidas.value.flatMap(id => recientes.value.filter(c => c.id === id)))
const intervalosCampanas = computed(() => campanasElegidas.value.map(c => {
  const t = totalesDe(c)
  const f = fraccion(t, metrica.value)
  const ic = metrica.value === 'envios' ? null : wilson(f.x, f.n)
  return { id: c.id, label: c.nombre, sub: `${c.f.toLocaleDateString('es-CO', { dateStyle: 'medium' })} · ${nf.format(c.totalEnvios)} enviados`, valor: valor(t, metrica.value), inf: ic?.inf ?? null, sup: ic?.sup ?? null }
}))
const parejas = computed(() => {
  const cs = campanasElegidas.value
  const r: { a: string; b: string; texto: string; signif: boolean }[] = []
  if (metrica.value === 'envios') return r
  for (let i = 0; i < cs.length; i++) for (let j = i + 1; j < cs.length; j++) {
    const fa = fraccion(totalesDe(cs[i]), metrica.value), fb = fraccion(totalesDe(cs[j]), metrica.value)
    const p = pruebaProporciones(fa.x, fa.n, fb.x, fb.n)
    r.push({ a: cs[i].nombre, b: cs[j].nombre, texto: textoPrueba(p), signif: !!p?.significativa })
  }
  return r
})

const segmentado = 'flex rounded-lg border border-default p-0.5 text-[11px] font-semibold bg-white dark:bg-slate-800'
const opcion = (activa: boolean) => ['h-7 px-2.5 rounded-md transition-colors whitespace-nowrap', activa ? 'bg-[#2447F9] text-white' : 'text-muted hover:text-heading']
const select = 'h-9 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[12px] text-body outline-none focus:border-[#2447F9] max-w-full'
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <div :class="segmentado" role="tablist" aria-label="Qué comparar">
        <button type="button" :class="opcion(modo === 'anios')" @click="modo = 'anios'">Años</button>
        <button type="button" :class="opcion(modo === 'meses')" @click="modo = 'meses'">Meses</button>
        <button type="button" :class="opcion(modo === 'campanas')" @click="modo = 'campanas'">Campañas</button>
      </div>
      <select v-model="metrica" :class="select" aria-label="Métrica">
        <option v-for="m in LISTA_METRICAS" :key="m" :value="m">{{ METRICAS[m].label }}</option>
      </select>
      <span class="text-[11px] text-muted">{{ METRICAS[metrica].ayuda }}</span>
    </div>

    <!-- ── Años ── -->
    <template v-if="modo === 'anios'">
      <div class="flex flex-wrap items-center gap-2 text-[12px] text-body">
        <select v-model.number="anioA" :class="select" aria-label="Año A"><option v-for="a in anios" :key="a" :value="a">{{ a }}</option></select>
        <span class="text-muted font-semibold">vs</span>
        <select v-model.number="anioB" :class="select" aria-label="Año B"><option v-for="a in [...anios, Math.min(...anios) - 1]" :key="a" :value="a">{{ a }}</option></select>
      </div>
      <section class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">{{ METRICAS[metrica].label }} mes a mes · {{ anioA }} vs {{ anioB }}</h3>
        <p class="text-[11px] text-muted mb-1">Cada franja es un mes. Un hueco = ese mes no hubo envíos.</p>
        <AyudaGrafico>
          <p>Sirve para ver si este año nos va mejor o peor que el anterior <strong>en el mismo mes</strong> (enero contra enero, etc.).</p>
          <ul>
            <li><strong>Cada color es un año.</strong> Si el punto de un año está más arriba, ese mes le fue mejor en {{ METRICAS[metrica].corto.toLowerCase() }}.</li>
            <li><strong>Punto suelto:</strong> ese mes hubo envíos pero el mes anterior y el siguiente no, por eso no se une con una línea.</li>
            <li><strong>Mes vacío:</strong> no hubo campañas. No significa 0%, significa "sin dato".</li>
            <li><strong>Línea que baja de golpe a 0%:</strong> casi siempre es una campaña de prueba o una sin seguimiento de aperturas. Use "Excluir pruebas" (arriba a la derecha) para quitarlas.</li>
            <li>Pase el mouse por un mes para ver los valores exactos, o use <strong>"Ver tabla"</strong>. Con "Unir huecos" verá la tendencia general del año.</li>
          </ul>
          <p>Para saber si la diferencia entre los dos años es real o casualidad, mire la tabla de abajo, columna <strong>"¿Es significativa?"</strong>.</p>
        </AyudaGrafico>
        <GraficoLineas :categorias="catMeses" :series="seriesAnios" :formato="METRICAS[metrica].pct ? 'pct' : 'numero'" />
      </section>
    </template>

    <!-- ── Meses ── -->
    <template v-else-if="modo === 'meses'">
      <div class="flex flex-wrap items-center gap-2 text-[12px] text-body">
        <select :value="claveMes(mesA)" :class="select" aria-label="Mes A" @change="mesA = desdeClave(($event.target as HTMLSelectElement).value)">
          <option v-for="o in opcionesMes" :key="o.valor" :value="o.valor">{{ o.label }}{{ o.n ? ` (${o.n})` : '' }}</option>
        </select>
        <span class="text-muted font-semibold">vs</span>
        <select :value="claveMes(mesB)" :class="select" aria-label="Mes B" @change="mesB = desdeClave(($event.target as HTMLSelectElement).value)">
          <option v-for="o in opcionesMes" :key="o.valor" :value="o.valor">{{ o.label }}{{ o.n ? ` (${o.n})` : '' }}</option>
        </select>
        <span class="text-[11px] text-muted">(entre paréntesis: campañas enviadas ese mes)</span>
      </div>
      <section class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">{{ METRICAS[metrica].label }} por día del mes</h3>
        <p class="text-[11px] text-muted mb-1">Día 1 a 31 de cada mes, según la fecha de envío de las campañas.</p>
        <AyudaGrafico>
          <p>Compara dos meses día por día: por ejemplo, este mes contra el mes pasado, o contra el mismo mes del año anterior.</p>
          <ul>
            <li>Cada punto es el resultado de las campañas <strong>enviadas ese día</strong> (las aperturas pueden haber llegado días después).</li>
            <li>Los días sin punto no tuvieron envíos.</li>
            <li>Útil para ver si enviar a <strong>inicio, mitad o fin de mes</strong> cambia los resultados.</li>
          </ul>
        </AyudaGrafico>
        <GraficoLineas :categorias="catDias" :series="seriesMeses" :formato="METRICAS[metrica].pct ? 'pct' : 'numero'" />
      </section>
    </template>

    <!-- Tabla A vs B (años o meses) -->
    <section v-if="modo !== 'campanas'" class="surface-card rounded-2xl shadow-sm overflow-hidden">
      <div class="px-4 py-3 border-b border-default">
        <h3 class="text-[13px] font-bold text-heading">
          {{ modo === 'anios' ? `${anioA} vs ${anioB}` : `${nombrePeriodo(mesA)} vs ${nombrePeriodo(mesB)}` }}
        </h3>
        <p class="text-[11px] text-muted mb-1">Prueba z de dos proporciones (95% de confianza): dice si la diferencia es real o puede ser azar.</p>
        <AyudaGrafico titulo="¿Qué significa «significativa»?">
          <p>Que una tasa suba o baje un poco no siempre quiere decir algo: los resultados varían naturalmente de una campaña a otra.</p>
          <ul>
            <li><strong>Diferencia:</strong> cuánto cambió. "pp" = puntos porcentuales: pasar de 30% a 35% es <strong>+5 pp</strong>.</li>
            <li><strong>Sí (significativa):</strong> la diferencia es real, no casualidad. Vale la pena tomar decisiones con ella.</li>
            <li><strong>No:</strong> la diferencia puede ser simple azar. No saque conclusiones todavía; espere más envíos.</li>
            <li><strong>p:</strong> la probabilidad de ver esa diferencia por pura casualidad. Menos de 0,05 (5%) = significativa.</li>
          </ul>
          <p>Ojo: con muchos correos, hasta una diferencia pequeña sale "significativa". Pregúntese también si el tamaño del cambio importa para el negocio.</p>
        </AyudaGrafico>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-[12px]">
          <thead>
            <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
              <th class="px-4 py-2.5 font-semibold">Métrica</th>
              <th class="px-3 py-2.5 font-semibold text-right">{{ modo === 'anios' ? anioA : nombrePeriodo(mesA) }}</th>
              <th class="px-3 py-2.5 font-semibold text-right">{{ modo === 'anios' ? anioB : nombrePeriodo(mesB) }}</th>
              <th class="px-3 py-2.5 font-semibold text-right">Diferencia</th>
              <th class="px-3 py-2.5 font-semibold">¿Es significativa?</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in (modo === 'anios' ? filasComparacion(totA, totB) : filasComparacion(totMesA, totMesB))" :key="f.m"
              class="border-b border-slate-100 dark:border-slate-800" :class="{ 'bg-blue-50/40 dark:bg-slate-700/30': f.m === metrica }">
              <td class="px-4 py-2.5 font-semibold text-heading">{{ METRICAS[f.m].label }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums text-body">{{ fmtM(f.m, f.va) }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums text-body">{{ fmtM(f.m, f.vb) }}</td>
              <td class="px-3 py-2.5 text-right tabular-nums font-bold text-heading">{{ f.delta }}</td>
              <td class="px-3 py-2.5 text-[11px]">
                <span v-if="f.prueba && f.prueba.significativa" class="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400 font-semibold"><CircleCheck :size="12" /> Sí · p {{ pValor(f.prueba.p) }}</span>
                <span v-else-if="f.prueba" class="inline-flex items-center gap-1 text-muted"><CircleHelp :size="12" /> No · p {{ pValor(f.prueba.p) }}</span>
                <span v-else class="text-muted">{{ f.m === 'envios' ? 'Conteo (sin prueba)' : 'Sin datos' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ── Campañas ── -->
    <template v-if="modo === 'campanas'">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
        <select v-for="(_, i) in elegidas" :key="i" v-model="elegidas[i]" :class="select" :aria-label="`Campaña ${i + 1}`">
          <option :value="null">{{ i < 2 ? 'Elegir campaña…' : '(opcional) tercera campaña' }}</option>
          <optgroup v-for="a in anios" :key="a" :label="String(a)">
            <option v-for="c in recientes.filter(c => c.anio === a)" :key="c.id" :value="c.id"
              :disabled="elegidas.includes(c.id) && elegidas[i] !== c.id">{{ c.nombre }} · {{ c.f.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' }) }} · {{ nf.format(c.totalEnvios) }}</option>
          </optgroup>
        </select>
      </div>
      <section class="surface-card rounded-2xl shadow-sm p-4">
        <h3 class="text-[13px] font-bold text-heading">{{ METRICAS[metrica].label }} con intervalo de confianza del 95%</h3>
        <p class="text-[11px] text-muted mb-3">La barra es el rango donde probablemente está la tasa real. Si las barras de dos campañas no se tocan, la diferencia es real; si se solapan mucho, puede ser azar.</p>
        <AyudaGrafico>
          <p>Sirve para comparar campañas de forma justa, aunque tengan tamaños muy distintos.</p>
          <ul>
            <li><strong>El punto</strong> es la tasa de la campaña.</li>
            <li><strong>La barra</strong> es el margen de error: la tasa "real" probablemente está dentro de ese rango.</li>
            <li><strong>Barra corta</strong> = campaña grande, el resultado es confiable. <strong>Barra larga</strong> = campaña pequeña, el resultado puede cambiar mucho.</li>
            <li>Si las barras de dos campañas <strong>no se tocan</strong>, una de verdad funcionó mejor que la otra. Si se cruzan, no se puede asegurar.</li>
          </ul>
          <p>Ejemplo de uso: probar dos asuntos distintos y ver cuál ganó de verdad.</p>
        </AyudaGrafico>
        <p v-if="metrica === 'envios'" class="text-[12px] text-muted py-4">Elija una tasa (apertura, clics, rebote…) para ver intervalos de confianza.</p>
        <IntervalosConfianza v-else :items="intervalosCampanas" />
        <ul v-if="parejas.length" class="mt-4 space-y-1.5 border-t border-default pt-3">
          <li v-for="p in parejas" :key="p.a + p.b" class="flex items-start gap-1.5 text-[11.5px]">
            <component :is="p.signif ? CircleCheck : CircleHelp" :size="13" class="mt-0.5 shrink-0" :class="p.signif ? 'text-emerald-600 dark:text-emerald-400' : 'text-muted'" />
            <span class="text-body"><strong class="text-heading">{{ p.a }}</strong> vs <strong class="text-heading">{{ p.b }}</strong>: {{ p.texto }}</span>
          </li>
        </ul>
      </section>
      <section class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-[12px]">
            <thead>
              <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
                <th class="px-4 py-2.5 font-semibold">Métrica</th>
                <th v-for="c in campanasElegidas" :key="c.id" class="px-3 py-2.5 font-semibold text-right max-w-[200px] truncate" :title="c.nombre">{{ c.nombre }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in LISTA_METRICAS" :key="m" class="border-b border-slate-100 dark:border-slate-800" :class="{ 'bg-blue-50/40 dark:bg-slate-700/30': m === metrica }">
                <td class="px-4 py-2.5 font-semibold text-heading">{{ METRICAS[m].label }}</td>
                <td v-for="c in campanasElegidas" :key="c.id" class="px-3 py-2.5 text-right tabular-nums text-body">{{ fmtM(m, valor(totalesDe(c), m)) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
