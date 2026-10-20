<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BarChart3, RefreshCw, Loader2, LayoutDashboard, GitCompareArrows, ChartBarBig, FlaskConical } from 'lucide-vue-next'
import { useEstadisticasCampanas } from '../composables/useEstadisticasCampanas'
import CampanasSubnav from '@/features/campanas/components/CampanasSubnav.vue'
import MigasCampanas from '@/features/campanas/components/MigasCampanas.vue'
import TabResumen from '../components/estadisticas/TabResumen.vue'
import TabComparar from '../components/estadisticas/TabComparar.vue'
import TabDistribucion from '../components/estadisticas/TabDistribucion.vue'
import AyudaGrafico from '../components/estadisticas/AyudaGrafico.vue'

// Estadísticas de las campañas de MailerTurbo en tres vistas:
// Resumen (año/mes/día/campaña), Comparar (años, meses, campañas) y Distribución.
const route = useRoute()
const router = useRouter()
const { todas, excluidas, minEnvios, cargando, error, cargar } = useEstadisticasCampanas()
onMounted(() => void cargar())

const VISTAS = [
  { id: 'resumen', label: 'Resumen', icono: LayoutDashboard, componente: TabResumen },
  { id: 'comparar', label: 'Comparar', icono: GitCompareArrows, componente: TabComparar },
  { id: 'distribucion', label: 'Distribución', icono: ChartBarBig, componente: TabDistribucion },
] as const
const vista = computed(() => VISTAS.find(v => v.id === route.query.vista) ?? VISTAS[0])
const irVista = (id: string) => router.replace({ query: { ...route.query, vista: id === 'resumen' ? undefined : id } })

const UMBRALES = [0, 10, 30, 100]
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
      <div>
        <MigasCampanas :migas="[{ label: 'Estadísticas', ruta: '/campanas/estadisticas' }, { label: vista.label }]" class="mb-1.5" />
        <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
          <BarChart3 :size="19" class="text-[#2447F9]" /> Estadísticas de campañas
        </h2>
        <p class="text-[12px] text-body mt-0.5">Resultados de los envíos de MailerTurbo por año, mes, día y campaña.</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <label class="flex items-center gap-1.5 h-9 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] text-body"
          title="Las campañas con muy pocos envíos (pruebas internas) distorsionan las tasas: 2 correos abiertos = 100%.">
          <FlaskConical :size="13" class="text-muted" />
          Excluir pruebas
          <select v-model.number="minEnvios" class="bg-transparent outline-none font-semibold">
            <option v-for="u in UMBRALES" :key="u" :value="u">{{ u ? `< ${u} envíos` : 'No' }}</option>
          </select>
        </label>
        <button
          @click="cargar(true)"
          :disabled="cargando"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
        ><RefreshCw :size="13" :class="{ 'animate-spin': cargando }" /> Actualizar</button>
      </div>
    </div>

    <CampanasSubnav />

    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex rounded-xl border border-default p-1 bg-white dark:bg-slate-800 gap-1" role="tablist" aria-label="Vista de estadísticas">
        <button
          v-for="v in VISTAS"
          :key="v.id"
          type="button"
          role="tab"
          :aria-selected="vista.id === v.id"
          class="flex items-center gap-1.5 h-8 px-3 rounded-lg text-[12px] font-semibold transition-colors"
          :class="vista.id === v.id ? 'bg-[#2447F9] text-white shadow-sm' : 'text-muted hover:text-heading hover:bg-slate-50 dark:hover:bg-slate-700'"
          @click="irVista(v.id)"
        ><component :is="v.icono" :size="14" /> {{ v.label }}</button>
      </div>
      <p v-if="excluidas" class="text-[11px] text-muted">
        {{ excluidas === 1 ? '1 campaña de prueba excluida' : `${excluidas} campañas de prueba excluidas` }} (menos de {{ minEnvios }} envíos).
      </p>
    </div>

    <AyudaGrafico titulo="Glosario: qué significa cada término">
      <ul>
        <li><strong>Tasa de apertura:</strong> de cada 100 correos enviados, cuántos se abrieron.</li>
        <li><strong>Tasa de clics (CTR):</strong> de cada 100 correos enviados, cuántos hicieron clic en algún enlace.</li>
        <li><strong>CTOR (clics sobre aperturas):</strong> de cada 100 personas que abrieron, cuántas hicieron clic. Mide si el contenido convence.</li>
        <li><strong>Rebote:</strong> correo que no llegó (dirección mal escrita, buzón lleno o inexistente).</li>
        <li><strong>Baja:</strong> persona que pidió no recibir más correos.</li>
        <li><strong>pp (puntos porcentuales):</strong> diferencia entre dos porcentajes. De 30% a 35% = +5 pp.</li>
        <li><strong>Significativo:</strong> la diferencia es real y no producto de la casualidad.</li>
        <li><strong>Promedio (media):</strong> la suma dividida entre la cantidad. Se deja arrastrar por valores extremos.</li>
        <li><strong>Mediana:</strong> el valor del medio: la mitad de las campañas está por debajo y la otra mitad por encima. Es más "justa" cuando hay casos extremos.</li>
        <li><strong>Campaña de prueba:</strong> envío muy pequeño (por ejemplo, a 2 o 3 correos internos). Se excluye para no distorsionar: 2 de 2 abiertos daría un 100% engañoso.</li>
      </ul>
    </AyudaGrafico>

    <p v-if="error" class="text-[12px] text-red-600 dark:text-red-400">{{ error }}</p>
    <div v-if="cargando && !todas.length" class="surface-card rounded-2xl py-16 text-center text-[12px] text-muted">
      <Loader2 :size="16" class="animate-spin inline mr-1" /> Consultando las campañas en MailerTurbo…
    </div>
    <component :is="vista.componente" v-else-if="todas.length" :key="vista.id" />
  </div>
</template>
