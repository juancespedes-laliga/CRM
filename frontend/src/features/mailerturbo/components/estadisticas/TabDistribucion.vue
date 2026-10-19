<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Info } from 'lucide-vue-next'
import {
  useEstadisticasCampanas, valor, sumar, totalesDe, MESES_CORTOS, METRICAS, type Metrica,
} from '../../composables/useEstadisticasCampanas'
import { resumen, esAtipico, interpretarForma } from '../../utils/estadistica'
import Histograma from '../graficos/Histograma.vue'
import DiagramaCajas, { type GrupoCaja } from '../graficos/DiagramaCajas.vue'
import AyudaGrafico from './AyudaGrafico.vue'

// Cómo se reparten las campañas: cada campaña aporta UN dato (su propia tasa).
const router = useRouter()
const { anios, validas } = useEstadisticasCampanas()
const nf = new Intl.NumberFormat('es-CO')

const anio = ref<number | null>(null)
const metrica = ref<Metrica>('apertura')
const agrupar = ref<'nada' | 'anio' | 'mes' | 'semana'>('nada')
const LISTA_METRICAS = Object.keys(METRICAS) as Metrica[]
const pct = computed(() => METRICAS[metrica.value].pct)
const fmt = (v: number) => (Number.isNaN(v) ? '—' : pct.value ? `${v.toLocaleString('es-CO', { maximumFractionDigits: 2 })}%` : nf.format(Math.round(v)))
const fmtNum = (v: number, d = 2) => (Number.isNaN(v) ? '—' : v.toLocaleString('es-CO', { maximumFractionDigits: d }))

const campanas = computed(() => validas.value.filter(c => anio.value === null || c.anio === anio.value))
const datos = computed(() => campanas.value.flatMap(c => {
  const v = valor(totalesDe(c), metrica.value)
  return v == null ? [] : [{ id: c.id, label: c.nombre, valor: v, c }]
}))
const r = computed(() => resumen(datos.value.map(d => d.valor)))
const ponderada = computed(() => valor(sumar(campanas.value), metrica.value))

const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
const grupos = computed<GrupoCaja[]>(() => {
  const ds = datos.value
  if (agrupar.value === 'nada') return [{ id: 'todas', label: anio.value ? String(anio.value) : 'Todas', datos: ds }]
  const mapa = new Map<string | number, GrupoCaja>()
  const clave = (d: typeof ds[number]) =>
    agrupar.value === 'anio' ? { id: d.c.anio, label: String(d.c.anio) }
      : agrupar.value === 'mes' ? { id: d.c.anio * 100 + d.c.mes, label: `${MESES_CORTOS[d.c.mes]} ${String(d.c.anio).slice(2)}` }
        : { id: (d.c.f.getDay() + 6) % 7, label: DIAS[d.c.f.getDay()] }
  for (const d of ds) {
    const k = clave(d)
    if (!mapa.has(k.id)) mapa.set(k.id, { id: k.id, label: k.label, datos: [] })
    mapa.get(k.id)!.datos.push(d)
  }
  return [...mapa.values()].sort((a, b) => Number(a.id) - Number(b.id))
})

const atipicos = computed(() => (r.value ? datos.value.filter(d => esAtipico(d.valor, r.value!)) : []))
const verCampana = (id: string | number) => router.push({ path: `/campanas/mailerturbo/${id}`, query: { desde: 'estadisticas' } })

const descriptivos = computed(() => {
  const x = r.value
  if (!x) return []
  return [
    { label: 'Campañas (n)', valor: nf.format(x.n), ayuda: 'Cantidad de datos.' },
    { label: 'Media', valor: fmt(x.media), ayuda: 'Promedio simple de las campañas (cada campaña pesa igual).' },
    { label: 'Media ponderada', valor: ponderada.value == null ? '—' : fmt(ponderada.value), ayuda: 'Total del periodo: las campañas grandes pesan más. Es la cifra de los indicadores.' },
    { label: 'Mediana', valor: fmt(x.mediana), ayuda: 'La mitad de las campañas está por debajo y la otra mitad por encima.' },
    { label: 'Desviación estándar', valor: fmt(x.desviacion), ayuda: 'Cuánto se alejan, en promedio, las campañas de la media.' },
    { label: 'Coef. de variación', valor: Number.isNaN(x.cv) ? '—' : `${fmtNum(x.cv, 1)}%`, ayuda: 'Desviación / media. Más de 30% = resultados muy dispares entre campañas.' },
    { label: 'Mínimo', valor: fmt(x.min), ayuda: '' },
    { label: 'Q1 (percentil 25)', valor: fmt(x.q1), ayuda: 'El 25% de las campañas está por debajo.' },
    { label: 'Q3 (percentil 75)', valor: fmt(x.q3), ayuda: 'El 75% de las campañas está por debajo.' },
    { label: 'Máximo', valor: fmt(x.max), ayuda: '' },
    { label: 'Rango intercuartílico', valor: fmt(x.iqr), ayuda: 'Q3 − Q1: el ancho del 50% central (la caja).' },
    { label: 'Asimetría', valor: fmtNum(x.asimetria), ayuda: '0 = simétrica; positiva = cola a la derecha; negativa = cola a la izquierda.' },
    { label: 'Curtosis (exceso)', valor: fmtNum(x.curtosis), ayuda: '0 = como la normal; positiva = más valores extremos.' },
  ]
})

const segmentado = 'flex rounded-lg border border-default p-0.5 text-[11px] font-semibold bg-white dark:bg-slate-800'
const opcion = (activa: boolean) => ['h-7 px-2.5 rounded-md transition-colors whitespace-nowrap', activa ? 'bg-[#2447F9] text-white' : 'text-muted hover:text-heading']
const select = 'h-9 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[12px] text-body outline-none focus:border-[#2447F9]'
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <select v-model="metrica" :class="select" aria-label="Métrica">
        <option v-for="m in LISTA_METRICAS" :key="m" :value="m">{{ METRICAS[m].label }}</option>
      </select>
      <select v-model="anio" :class="select" aria-label="Año">
        <option :value="null">Todos los años</option>
        <option v-for="a in anios" :key="a" :value="a">{{ a }}</option>
      </select>
      <span class="text-[11px] text-muted">Cada campaña es un dato ({{ METRICAS[metrica].ayuda }}).</span>
    </div>

    <p v-if="!r" class="surface-card rounded-2xl px-4 py-6 text-center text-[12px] text-muted">No hay campañas para analizar.</p>

    <template v-else>
      <AyudaGrafico titulo="¿Para qué sirve esta pestaña?">
        <p>Las otras pestañas muestran totales. Esta muestra <strong>qué tan parecidas o distintas son las campañas entre sí</strong>, para responder preguntas como:</p>
        <ul>
          <li>¿Cuál es un resultado <strong>normal</strong> para nosotros? (sirve para fijar metas realistas).</li>
          <li>¿Nuestras campañas son <strong>consistentes</strong> o unas salen muy bien y otras muy mal?</li>
          <li>¿Qué campañas fueron <strong>excepcionales</strong> (para copiar lo que hicieron) o <strong>problemáticas</strong> (para revisarlas)?</li>
          <li>¿Influye el <strong>día de la semana</strong> o el mes en que enviamos?</li>
        </ul>
        <p>Aquí cada campaña cuenta como un dato, sin importar su tamaño.</p>
      </AyudaGrafico>

      <!-- Interpretación -->
      <div class="surface-card rounded-2xl shadow-sm px-4 py-3 flex items-start gap-2.5">
        <Info :size="15" class="text-[#2447F9] shrink-0 mt-0.5" />
        <div class="text-[12px] text-body leading-relaxed">
          <p>
            La {{ METRICAS[metrica].label.toLowerCase() }} típica es <strong class="text-heading">{{ fmt(r.mediana) }}</strong> (mediana);
            la mitad de las campañas está entre <strong class="text-heading">{{ fmt(r.q1) }}</strong> y <strong class="text-heading">{{ fmt(r.q3) }}</strong>.
            <template v-if="ponderada != null && pct"> Sumando todos los correos, la tasa global es <strong class="text-heading">{{ fmt(ponderada) }}</strong>.</template>
          </p>
          <p class="mt-1">{{ interpretarForma(r) }}</p>
          <p v-if="atipicos.length" class="mt-1">
            {{ atipicos.length === 1 ? 'Hay 1 campaña atípica' : `Hay ${atipicos.length} campañas atípicas` }}:
            <template v-for="(a, i) in atipicos" :key="a.id">
              <button type="button" class="font-semibold text-[#2447F9] hover:underline" @click="verCampana(a.id)">{{ a.label }} ({{ fmt(a.valor) }})</button><template v-if="i < atipicos.length - 1">, </template>
            </template>.
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-4 items-start">
        <section class="surface-card rounded-2xl shadow-sm p-4">
          <h3 class="text-[13px] font-bold text-heading">Histograma y campana de Gauss</h3>
          <p class="text-[11px] text-muted mb-3">
            Cuántas campañas caen en cada intervalo (regla de Sturges). La curva es la distribución normal con la misma media y desviación:
            si las barras siguen la curva, los datos son "normales". La franja sombreada es media ± 1 desviación (ahí cae el 68% en una normal).
          </p>
          <AyudaGrafico>
            <ul>
              <li><strong>Cada barra</strong> agrupa las campañas que tuvieron un resultado parecido. Ejemplo: la barra "30%–40%" con un 5 = cinco campañas abrieron entre 30% y 40%.</li>
              <li><strong>La barra más alta</strong> es el resultado más común: lo "normal" para nosotros.</li>
              <li><strong>La curva naranja (campana de Gauss)</strong> es cómo se verían las barras si los resultados fueran perfectamente "normales". Si las barras siguen la curva, el promedio es un buen resumen. Si no, guíese por la mediana.</li>
              <li><strong>Línea negra (media)</strong> = el promedio. <strong>Línea verde (mediana)</strong> = el valor del medio. Si están muy separadas, hay campañas extremas que mueven el promedio.</li>
              <li><strong>Franja sombreada:</strong> el rango donde cae la mayoría (2 de cada 3 campañas). Una campaña por encima es de las mejores; por debajo, conviene revisarla.</li>
            </ul>
            <p>Pase el mouse por una barra para ver qué campañas contiene.</p>
          </AyudaGrafico>
          <Histograma :datos="datos" :formato="pct ? 'pct' : 'numero'" />
        </section>

        <section class="surface-card rounded-2xl shadow-sm overflow-hidden">
          <div class="px-4 py-3 border-b border-default">
            <h3 class="text-[13px] font-bold text-heading">Estadística descriptiva</h3>
            <p class="text-[11px] text-muted">Pase el mouse por cada fila para ver qué significa.</p>
          </div>
          <dl class="divide-y divide-slate-100 dark:divide-slate-700/60">
            <div v-for="d in descriptivos" :key="d.label" class="flex items-center justify-between gap-3 px-4 py-1.5 text-[12px]" :title="d.ayuda">
              <dt class="text-muted">{{ d.label }}</dt>
              <dd class="font-semibold text-heading tabular-nums">{{ d.valor }}</dd>
            </div>
          </dl>
        </section>
      </div>

      <section class="surface-card rounded-2xl shadow-sm p-4">
        <div class="flex flex-wrap items-start justify-between gap-2 mb-3">
          <div>
            <h3 class="text-[13px] font-bold text-heading">Diagrama de cajas</h3>
            <p class="text-[11px] text-muted">Compara la dispersión entre grupos. Clic en un punto para abrir la campaña.</p>
          </div>
          <div :class="segmentado" role="tablist" aria-label="Agrupar">
            <button type="button" :class="opcion(agrupar === 'nada')" @click="agrupar = 'nada'">Sin agrupar</button>
            <button type="button" :class="opcion(agrupar === 'anio')" @click="agrupar = 'anio'">Por año</button>
            <button type="button" :class="opcion(agrupar === 'mes')" @click="agrupar = 'mes'">Por mes</button>
            <button type="button" :class="opcion(agrupar === 'semana')" @click="agrupar = 'semana'">Por día de la semana</button>
          </div>
        </div>
        <AyudaGrafico>
          <p>Resume en una sola figura cómo se reparten los resultados de un grupo de campañas, y permite comparar grupos (años, meses, días de la semana).</p>
          <ul>
            <li><strong>La caja</strong> contiene a la mitad de las campañas, las del medio. <strong>Caja angosta</strong> = resultados parecidos y predecibles. <strong>Caja ancha</strong> = resultados muy variables.</li>
            <li><strong>La raya dentro de la caja</strong> es la mediana: el resultado típico del grupo.</li>
            <li><strong>El rombo naranja</strong> es el promedio.</li>
            <li><strong>Las líneas a los lados (bigotes)</strong> llegan hasta los resultados más bajos y más altos que todavía se consideran normales.</li>
            <li><strong>Los puntos naranjas sueltos</strong> son campañas atípicas: salieron mucho mejor o mucho peor que el resto. Haga clic para abrirlas y ver qué tuvieron de distinto.</li>
          </ul>
          <p>Ejemplo de uso: agrupe <strong>"Por día de la semana"</strong>. Si la caja de un día queda claramente más a la derecha, ese día suele funcionar mejor para enviar.</p>
        </AyudaGrafico>
        <DiagramaCajas :grupos="grupos" :formato="pct ? 'pct' : 'numero'" @seleccionar="d => verCampana(d.id)" />
        <p v-if="agrupar !== 'nada' && grupos.some(g => g.datos.length < 5)" class="text-[10.5px] text-muted mt-2">
          Los grupos con menos de 5 campañas dan cajas poco confiables: tómelas como referencia, no como conclusión.
        </p>
      </section>
    </template>
  </div>
</template>
