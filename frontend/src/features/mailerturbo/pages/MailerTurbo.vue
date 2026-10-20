<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Megaphone, Send, CloudUpload, RefreshCw, Search, Loader2, ListPlus, ExternalLink, ChevronRight, ChevronLeft, BarChart3, X,
} from 'lucide-vue-next'
import type { CampanaMT } from '../types/mailerturbo'
import { abrirMailerTurbo, getCampanas } from '../services/mailerturbo.api'
import { useCatalogosMailerturbo } from '../composables/useCatalogosMailerturbo'
import { permisosDeModulo, tienePermiso } from '@/features/auth/composables/useAuth'
import CampanasSubnav from '@/features/campanas/components/CampanasSubnav.vue'
import EnviarCampanaDialog from '../dialogs/EnviarCampanaDialog.vue'
import SubirContactosDialog from '../dialogs/SubirContactosDialog.vue'
import MigasCampanas from '@/features/campanas/components/MigasCampanas.vue'
import Paginador from '../components/Paginador.vue'
import UsoMensualMailerTurbo from '../components/UsoMensualMailerTurbo.vue'

const router = useRouter()
const { gestionar: puedeGestionar } = permisosDeModulo('mailerturbo')
const puedeEnviar = tienePermiso('mailerturbo:enviar')
const nf = new Intl.NumberFormat('es-CO')
const fmtPct = (n: number) => `${Number(n || 0).toLocaleString('es-CO', { maximumFractionDigits: 1 })}%`
const verCampana = (id: number | string) => router.push(`/campanas/mailerturbo/${id}`)

// ── Listas (paginadas en el navegador) ───────────────────────────────
const { listas, cargando: cargandoListas, error: errorListas, cargar, nuevaLista } = useCatalogosMailerturbo()
const LISTAS_POR_PAGINA = 8
const busquedaLista = ref('')
const verArchivadas = ref(false)
const paginaListas = ref(1)
const listasFiltradas = computed(() => {
  const q = busquedaLista.value.trim().toLowerCase()
  return listas.value
    .filter(l => verArchivadas.value || l.estado === 'Activa')
    .filter(l => !q || l.titulo.toLowerCase().includes(q))
})
const totalPaginasListas = computed(() => Math.max(1, Math.ceil(listasFiltradas.value.length / LISTAS_POR_PAGINA)))
const listasVisibles = computed(() =>
  listasFiltradas.value.slice((paginaListas.value - 1) * LISTAS_POR_PAGINA, paginaListas.value * LISTAS_POR_PAGINA),
)
watch([busquedaLista, verArchivadas], () => { paginaListas.value = 1 })
const listasActivas = computed(() => listas.value.filter(l => l.estado === 'Activa').length)

const creandoLista = ref(false)
const tituloLista = ref('')
const guardandoLista = ref(false)
const errorLista = ref<string | null>(null)
async function confirmarNuevaLista() {
  if (!tituloLista.value.trim()) return
  guardandoLista.value = true
  errorLista.value = null
  try {
    await nuevaLista(tituloLista.value)
    tituloLista.value = ''
    creandoLista.value = false
  } catch (e) {
    errorLista.value = e instanceof Error ? e.message : 'No se pudo crear la lista.'
  } finally {
    guardandoLista.value = false
  }
}

// ── Campañas (paginadas en MailerTurbo) ──────────────────────────────
const porPagina = ref(10)
const campanas = ref<CampanaMT[]>([])
const totalCampanas = ref(0)
const totalPaginas = ref(1)
const pagina = ref(1)
const busquedaCampana = ref('')
const cargandoCampanas = ref(false)
const errorCampanas = ref<string | null>(null)
const actualizadoEn = ref<Date | null>(null)

// silencioso: sin esqueleto de carga (lo usa el refresco automático).
async function cargarCampanas(p = pagina.value, silencioso = false) {
  if (!silencioso) cargandoCampanas.value = true
  errorCampanas.value = null
  try {
    const r = await getCampanas(p, porPagina.value, busquedaCampana.value)
    campanas.value = r.campanas
    totalCampanas.value = r.total
    totalPaginas.value = Math.max(1, r.totalPaginas)
    pagina.value = p
    actualizadoEn.value = new Date()
  } catch (e) {
    errorCampanas.value = e instanceof Error ? e.message : 'No se pudieron cargar las campañas.'
  } finally {
    cargandoCampanas.value = false
  }
}
watch(porPagina, () => void cargarCampanas(1))

let temporizadorBusqueda: ReturnType<typeof setTimeout> | undefined
const onBuscarCampana = () => {
  clearTimeout(temporizadorBusqueda)
  temporizadorBusqueda = setTimeout(() => void cargarCampanas(1), 400)
}
const limpiarBusqueda = () => { busquedaCampana.value = ''; void cargarCampanas(1) }

const usoMensual = ref<InstanceType<typeof UsoMensualMailerTurbo> | null>(null)
const actualizarTodo = () => { void cargar(true); void cargarCampanas(); void usoMensual.value?.cargar() }
onMounted(() => { void cargar(); void cargarCampanas(1) })

// Mientras alguna campaña de la página se esté enviando, se refresca sola cada 30 s.
const ESTADOS_EN_CURSO = ['En proceso', 'Enviando']
const hayEnCurso = computed(() => campanas.value.some(c => ESTADOS_EN_CURSO.includes(c.estado)))
const autoRefresco = setInterval(() => {
  if (hayEnCurso.value && !cargandoCampanas.value) void cargarCampanas(pagina.value, true)
}, 30_000)
onUnmounted(() => clearInterval(autoRefresco))
const fmtHora = (d: Date) => d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

const COLOR_ESTADO: Record<string, string> = {
  Enviada: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300',
  Enviando: 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
  'En proceso': 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
  'En espera': 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300',
  Programada: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300',
  Borrador: 'bg-slate-100 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300',
}
const claseEstado = (estado: string) => COLOR_ESTADO[estado] ?? COLOR_ESTADO.Borrador
const fmtFecha = (f: string | null) => f ? new Date(f.replace(' ', 'T')).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' }) : 'Sin fecha'

// ── Abrir la plataforma con la sesión iniciada (token reutilizado hasta que vence) ──
const abriendo = ref(false)
const errorAbrir = ref<string | null>(null)
async function abrirPlataforma() {
  abriendo.value = true
  errorAbrir.value = null
  try {
    await abrirMailerTurbo()
  } catch (e) {
    errorAbrir.value = e instanceof Error ? e.message : 'No se pudo abrir MailerTurbo.'
  } finally {
    abriendo.value = false
  }
}

// ── Diálogos ─────────────────────────────────────────────────────────
const enviarVisible = ref(false)
const subirVisible = ref(false)
const onEnviada = () => { void cargarCampanas(1); void usoMensual.value?.cargar() }
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <MigasCampanas :migas="[{ label: 'Listas y campañas' }]" class="mb-1.5" />
        <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
          <Megaphone :size="19" class="text-[#2447F9]" /> Listas y campañas
        </h2>
        <p class="text-[12px] text-body mt-0.5">Envíos masivos de correo: listas de contactos, campañas y resultados.</p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700"
          @click="router.push('/campanas/estadisticas')"
        ><BarChart3 :size="13" /> Estadísticas</button>
        <button
          v-if="puedeGestionar"
          type="button"
          :disabled="abriendo"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
          :title="errorAbrir || 'Abre la plataforma con la sesión ya iniciada'"
          @click="abrirPlataforma"
        ><Loader2 v-if="abriendo" :size="13" class="animate-spin" /><ExternalLink v-else :size="13" /> Abrir MailerTurbo</button>
        <button
          @click="actualizarTodo"
          :disabled="cargandoListas || cargandoCampanas"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
          title="Volver a consultar MailerTurbo"
        ><RefreshCw :size="13" :class="{ 'animate-spin': cargandoListas || cargandoCampanas }" /> Actualizar</button>
        <button
          v-if="puedeGestionar"
          @click="subirVisible = true"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        ><CloudUpload :size="13" /> Subir contactos</button>
        <button
          v-if="puedeEnviar"
          @click="enviarVisible = true"
          class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all"
        ><Send :size="13" /> Nueva campaña</button>
      </div>
    </div>
    <p v-if="errorAbrir" class="text-[11px] text-red-500 -mt-3">{{ errorAbrir }}</p>

    <CampanasSubnav />

    <UsoMensualMailerTurbo ref="usoMensual" />

    <div class="grid grid-cols-1 xl:grid-cols-[300px_1fr] gap-4 items-start">
      <!-- Listas -->
      <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-default flex items-center justify-between gap-2">
          <div>
            <h3 class="text-[13px] font-bold text-heading">Listas</h3>
            <p class="text-[11px] text-muted">{{ listasActivas }} activas de {{ listas.length }}</p>
          </div>
          <button
            v-if="puedeGestionar"
            @click="creandoLista = !creandoLista; errorLista = null"
            class="flex items-center gap-1 h-8 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700"
          ><ListPlus :size="13" /> Nueva</button>
        </div>
        <div v-if="creandoLista" class="px-4 py-3 border-b border-default space-y-2">
          <input
            v-model="tituloLista"
            placeholder="Nombre de la lista"
            class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]"
            @keydown.enter="confirmarNuevaLista"
          />
          <p v-if="errorLista" class="text-[11px] text-red-500">{{ errorLista }}</p>
          <div class="flex justify-end gap-2">
            <button @click="creandoLista = false" class="h-8 px-3 rounded-lg border border-default text-[11px] font-semibold text-body">Cancelar</button>
            <button
              @click="confirmarNuevaLista"
              :disabled="!tituloLista.trim() || guardandoLista"
              class="h-8 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold disabled:opacity-50"
            >{{ guardandoLista ? 'Creando…' : 'Crear' }}</button>
          </div>
        </div>
        <div class="flex items-center gap-2 px-4 h-9 border-b border-default">
          <Search :size="13" class="text-muted shrink-0" />
          <input v-model="busquedaLista" placeholder="Buscar lista…" class="flex-1 min-w-0 bg-transparent text-[12px] outline-none text-body" />
          <label class="flex items-center gap-1 text-[10px] text-muted whitespace-nowrap cursor-pointer" title="Mostrar también las listas archivadas o inactivas">
            <input v-model="verArchivadas" type="checkbox" class="accent-[#2447F9]" /> Inactivas
          </label>
        </div>
        <div v-if="errorListas" class="px-4 py-3 text-[12px] text-red-600 dark:text-red-400">{{ errorListas }}</div>
        <div v-else-if="cargandoListas && !listas.length" class="px-4 py-8 text-center text-[12px] text-muted">
          <Loader2 :size="14" class="animate-spin inline mr-1" /> Cargando listas…
        </div>
        <ul v-else class="divide-y divide-slate-100 dark:divide-slate-700">
          <li v-for="l in listasVisibles" :key="l.id" class="px-4 py-2.5" :class="{ 'opacity-50': l.estado !== 'Activa' }">
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <div class="text-[12px] font-semibold text-heading truncate" :title="l.titulo">{{ l.titulo }}</div>
                <div class="text-[10px] text-muted">#{{ l.id }} · {{ l.estado }}</div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-[12px] font-bold text-heading tabular-nums">{{ nf.format(l.totalCorreos) }}</div>
                <div class="text-[10px] text-muted tabular-nums">{{ nf.format(l.totalActivos) }} activos</div>
              </div>
            </div>
          </li>
          <li v-if="!listasFiltradas.length" class="px-4 py-8 text-center text-[12px] text-muted">No hay listas.</li>
        </ul>
        <div v-if="totalPaginasListas > 1" class="px-4 py-2 border-t border-default flex items-center justify-between text-[11px] text-muted">
          <span class="tabular-nums">{{ paginaListas }} / {{ totalPaginasListas }}</span>
          <div class="flex gap-1">
            <button :disabled="paginaListas <= 1" class="w-7 h-7 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center disabled:opacity-40" title="Anterior" @click="paginaListas--"><ChevronLeft :size="13" /></button>
            <button :disabled="paginaListas >= totalPaginasListas" class="w-7 h-7 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center disabled:opacity-40" title="Siguiente" @click="paginaListas++"><ChevronRight :size="13" /></button>
          </div>
        </div>
      </div>

      <!-- Campañas -->
      <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-default flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 class="text-[13px] font-bold text-heading">Campañas</h3>
            <p class="text-[11px] text-muted">{{ nf.format(totalCampanas) }} en total, las más recientes primero. Clic en una para ver sus destinatarios.</p>
            <p v-if="actualizadoEn" class="text-[10px] text-subtle mt-0.5">
              Actualizado a las {{ fmtHora(actualizadoEn) }}<template v-if="hayEnCurso"> · hay campañas enviándose, se actualiza sola cada 30 s</template>
            </p>
          </div>
          <div class="flex items-center gap-2 h-9 px-3 rounded-lg input-surface w-full sm:w-64">
            <Search :size="13" class="text-muted shrink-0" />
            <input v-model="busquedaCampana" @input="onBuscarCampana" placeholder="Buscar por nombre o asunto…" class="flex-1 min-w-0 bg-transparent text-[12px] outline-none text-body" />
            <button v-if="busquedaCampana" type="button" class="text-muted hover:text-heading" title="Limpiar" @click="limpiarBusqueda"><X :size="12" /></button>
          </div>
        </div>

        <div v-if="errorCampanas" class="px-4 py-3 text-[12px] text-red-600 dark:text-red-400">{{ errorCampanas }}</div>

        <div class="overflow-x-auto">
          <table class="w-full text-[12px]">
            <thead>
              <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
                <th class="px-4 py-2.5 font-semibold">Campaña</th>
                <th class="px-3 py-2.5 font-semibold">Estado</th>
                <th class="px-3 py-2.5 font-semibold text-right">Envíos</th>
                <th class="px-3 py-2.5 font-semibold text-right">Aperturas</th>
                <th class="px-3 py-2.5 font-semibold text-right">Clics</th>
                <th class="px-3 py-2.5 font-semibold text-right">Rebotes</th>
                <th class="px-3 py-2.5 font-semibold text-right">Bajas</th>
                <th class="w-8" />
              </tr>
            </thead>
            <tbody>
              <template v-if="cargandoCampanas">
                <tr v-for="n in Math.min(porPagina, 6)" :key="n" class="border-b border-slate-100 dark:border-slate-800">
                  <td colspan="8" class="px-4 py-3"><div class="h-8 rounded-lg bg-slate-100 dark:bg-slate-700/60 animate-pulse" /></td>
                </tr>
              </template>
              <template v-else>
                <tr
                  v-for="c in campanas"
                  :key="c.id"
                  tabindex="0"
                  class="group border-b border-slate-100 dark:border-slate-800 align-top cursor-pointer hover:bg-blue-50/50 dark:hover:bg-slate-700/40 focus-visible:outline-2 focus-visible:outline-[#2447F9]"
                  @click="verCampana(c.id)"
                  @keydown.enter="verCampana(c.id)"
                >
                  <td class="px-4 py-2.5 min-w-[220px] max-w-[320px]">
                    <div class="font-semibold text-heading truncate group-hover:text-[#2447F9]" :title="c.nombre">{{ c.nombre }}</div>
                    <div class="text-[11px] text-muted truncate" :title="c.asunto || ''">{{ c.asunto || 'Sin asunto' }}</div>
                    <div class="text-[10px] text-subtle mt-0.5 truncate">#{{ c.id }} · {{ fmtFecha(c.fecha) }}<template v-if="c.listas"> · {{ c.listas }}</template></div>
                  </td>
                  <td class="px-3 py-2.5 whitespace-nowrap">
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-md" :class="claseEstado(c.estado)">{{ c.estado }}</span>
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums font-semibold text-heading">{{ nf.format(c.totalEnvios) }}</td>
                  <td class="px-3 py-2.5 text-right tabular-nums">
                    <div class="text-body">{{ nf.format(c.totalVistas) }}</div>
                    <div class="text-[10px] text-muted">{{ fmtPct(c.porcentajeVistas) }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums">
                    <div class="text-body">{{ nf.format(c.totalClicks) }}</div>
                    <div class="text-[10px] text-muted">{{ fmtPct(c.porcentajeClicks) }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-right tabular-nums text-body">{{ nf.format(c.totalRebotes) }}</td>
                  <td class="px-3 py-2.5 text-right tabular-nums text-body">{{ nf.format(c.totalSalidas) }}</td>
                  <td class="pr-3 py-2.5 text-muted group-hover:text-[#2447F9]"><ChevronRight :size="15" /></td>
                </tr>
                <tr v-if="!campanas.length && !errorCampanas">
                  <td colspan="8" class="px-4 py-10 text-center text-muted">{{ busquedaCampana ? 'Ninguna campaña coincide con la búsqueda.' : 'No hay campañas.' }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <div class="px-4 py-2.5 border-t border-default">
          <Paginador
            :pagina="pagina"
            v-model:por-pagina="porPagina"
            :opciones-por-pagina="[10, 25, 50]"
            :total-paginas="totalPaginas"
            :total="totalCampanas"
            :deshabilitado="cargandoCampanas"
            @update:pagina="p => cargarCampanas(p)"
          />
        </div>
      </div>
    </div>

    <EnviarCampanaDialog v-model:visible="enviarVisible" @enviada="onEnviada" />
    <SubirContactosDialog v-model:visible="subirVisible" />
  </div>
</template>
