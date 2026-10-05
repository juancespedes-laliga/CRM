<script setup lang="ts">
import { computed, onActivated, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight, ChevronLeft, RefreshCw, SlidersHorizontal, PanelLeftOpen, Send, X, Mail, Phone, Bookmark, Check, Loader2, Info, UsersRound } from 'lucide-vue-next'
import { clonarFiltro, resumirFiltros } from '../constants/ciclo-afiliado.constants'
import { getSegmentoPreseleccionado } from '../composables/useSegmentoPreseleccionado'
import { useSegmentosGuardados } from '../composables/useSegmentosGuardados'
import { useSegmentador } from '../composables/useSegmentador'
import FiltrosSegmento from '../components/FiltrosSegmento.vue'
import EnviarSegmentoDialog from '../components/EnviarSegmentoDialog.vue'
import UsoPlanPanel from '../components/UsoPlanPanel.vue'
import AudienciasSubnav from '../components/AudienciasSubnav.vue'
import AgregarAGrupoDialog from '@/features/grupos-interes/dialogs/AgregarAGrupoDialog.vue'
import type { PersonaParaGrupo } from '@/features/grupos-interes/types/grupo'

const router = useRouter()
const nf = new Intl.NumberFormat('es-CO')

const {
  f, fApp, sel, filtrados, seleccion, todoSel, nFiltros,
  total, pagina, totalPaginas, rangoDesde, rangoHasta,
  cargando, cargandoBloque, error,
  aplicar: aplicarFiltro, limpiar, precargar, toggleRow, toggleTodo,
  paginaAnterior, paginaSiguiente,
} = useSegmentador()

const mostrarFiltros = ref(false)
/** En desktop: oculta el panel izquierdo para ceder el ancho a la tabla. */
const filtrosColapsados = ref(false)
const aplicar = async () => {
  await aplicarFiltro()
  mostrarFiltros.value = false
}

const revisarPreseleccion = () => {
  const pre = getSegmentoPreseleccionado()
  if (pre) void precargar(pre)
}
revisarPreseleccion()
onActivated(revisarPreseleccion)

const conCorreo = computed(() => seleccion.value.filter(a => a.tieneCorreo).length)
const conCelular = computed(() => seleccion.value.filter(a => a.tieneCelular).length)

const formatearDocumento = (doc: string) => {
  const n = Number(doc)
  return doc && Number.isFinite(n) ? nf.format(n) : doc
}

const ultimoUsoTxt = (d: number | null) => d === null ? 'Nunca' : `hace ${d} d`
const ultimoUsoCls = (d: number | null) => d === null || d > 90 ? 'text-red-500 dark:text-red-400'
  : d > 45 ? 'text-amber-600 dark:text-amber-400' : 'text-muted'
const sexoTxt = (s: string | null) => (s === 'F' ? 'Mujer' : s === 'M' ? 'Hombre' : '')
const detallePersona = (a: { sexo: string | null; edad: number | null }) =>
  [sexoTxt(a.sexo), a.edad !== null ? `${a.edad} años` : ''].filter(Boolean).join(' · ')

// Filtros APLICADOS (no el borrador del panel) como etiquetas legibles en la barra superior.
const criteriosAplicados = computed(() => resumirFiltros(fApp.value))

// Personas seleccionadas -> grupo de interés (ver features/grupos-interes).
const agregarGrupoVisible = ref(false)
const ciudadDe = (direccion: string) => (direccion === '—' ? '' : direccion.split(' · ')[0])
const personasParaGrupo = computed<PersonaParaGrupo[]>(() => seleccion.value.map(a => ({
  documento: a.documento, nombre: a.nombre, correo: a.correo, telefono: a.telefono, ciudad: ciudadDe(a.direccion),
})))

const enviarVisible = ref(false)

const { guardar } = useSegmentosGuardados()
const guardarVisible = ref(false)
const nombreSegmento = ref('')
const guardado = ref(false)
const abrirGuardar = () => { nombreSegmento.value = ''; guardado.value = false; guardarVisible.value = true }
const confirmarGuardar = () => {
  if (!nombreSegmento.value.trim()) return
  guardar({
    nombre: nombreSegmento.value,
    filtros: clonarFiltro(fApp.value),
    criterios: resumirFiltros(fApp.value),
    personas: seleccion.value.length,
    conCorreo: conCorreo.value,
    conCelular: conCelular.value,
  })
  guardado.value = true
  setTimeout(() => { guardarVisible.value = false }, 1200)
}
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div>
      <nav class="flex items-center gap-1.5 text-[12px] mb-1.5">
        <span class="text-slate-400 dark:text-slate-500">CRM Mercadeo</span>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <button class="text-slate-400 dark:text-slate-500 hover:text-[#2447F9] font-semibold transition-colors" @click="router.push('/embudos')">Embudos</button>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <span class="font-bold text-[#0F172A] dark:text-slate-100">Audiencias</span>
      </nav>
      <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
        <RefreshCw :size="19" class="text-[#EC4899]" /> Audiencias
      </h2>
      <p class="text-[12px] text-body mt-0.5">
        Arma una audiencia con filtros de Plan Liga (o no Plan Liga) y actúa sobre ella, o trabaja con grupos de interés: listas fijas con categorías propias.
      </p>
    </div>

    <AudienciasSubnav />

    <!-- Solo cuando el filtro APLICADO (fApp, no el borrador f) es "Plan Liga": el
    resumen/buscador es especifico de esa audiencia, no tiene sentido con "No plan
    Liga" ni sin filtro de plan elegido. -->
    <UsoPlanPanel v-if="fApp.planLiga === 'Plan Liga'" />

    <button
      class="lg:hidden flex items-center gap-1.5 h-9 px-3 rounded-md border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body"
      @click="mostrarFiltros = !mostrarFiltros"
    >
      <SlidersHorizontal :size="13" /> Filtros de segmento
      <span v-if="nFiltros" class="bg-[#2447F9] text-white text-[9px] font-bold px-1.5 rounded-sm">{{ nFiltros }}</span>
    </button>

    <div class="flex flex-col lg:flex-row gap-4">
      <aside
        class="w-full lg:w-72 shrink-0 transition-[width,opacity] duration-200"
        :class="[
          mostrarFiltros ? 'block' : 'hidden',
          filtrosColapsados ? 'lg:hidden' : 'lg:block',
        ]"
      >
        <FiltrosSegmento
          v-model="f"
          @aplicar="aplicar"
          @limpiar="limpiar"
          @colapsar="filtrosColapsados = true"
        />
      </aside>

      <div class="flex-1 min-w-0 flex flex-col gap-4 lg:h-[calc(100vh-190px)]">
        <!-- Barra de la audiencia: totales, filtros aplicados y acciones -->
        <div class="surface-card rounded-xl shadow-sm shrink-0">
          <div class="px-4 py-3 flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3 flex-wrap">
              <button
                v-if="filtrosColapsados"
                type="button"
                class="hidden lg:inline-flex items-center gap-1.5 h-8 px-2.5 rounded-md border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:border-slate-400 transition-colors"
                title="Mostrar filtros"
                @click="filtrosColapsados = false"
              >
                <PanelLeftOpen :size="13" /> Filtros
                <span v-if="nFiltros" class="bg-[#2447F9] text-white text-[9px] font-bold px-1.5 rounded-sm">{{ nFiltros }}</span>
              </button>
              <div class="flex items-baseline gap-1.5">
                <Loader2 v-if="cargando" :size="14" class="animate-spin text-[#2447F9] self-center" />
                <span class="text-[18px] font-bold text-heading tabular-nums">{{ nf.format(total) }}</span>
                <span class="text-[12px] text-muted">personas</span>
              </div>
              <span class="h-5 w-px bg-slate-200 dark:bg-slate-700" />
              <span class="text-[12px] text-muted"><strong class="text-heading tabular-nums">{{ nf.format(seleccion.length) }}</strong> seleccionadas</span>
              <span v-if="cargandoBloque" class="flex items-center gap-1.5 text-[11px] font-semibold text-[#2447F9]">
                <Loader2 :size="12" class="animate-spin" /> cargando más…
              </span>
            </div>
            <div class="flex items-center gap-2 flex-wrap">
              <button
                @click="abrirGuardar"
                :disabled="!seleccion.length || cargando"
                class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
              ><Bookmark :size="13" /> Guardar segmento</button>
              <button
                @click="agregarGrupoVisible = true"
                :disabled="!seleccion.length || cargando"
                class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
              ><UsersRound :size="13" /> Agregar a grupo de interés</button>
              <button
                @click="enviarVisible = true"
                :disabled="!seleccion.length || cargando"
                title="Vista previa: el envío real de correos/WhatsApp todavía no está conectado."
                class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow-sm hover:bg-[#1D3DD9] transition-colors disabled:opacity-50"
              ><Send :size="13" /> Enviar</button>
            </div>
          </div>
          <div v-if="criteriosAplicados.length" class="px-4 py-2 border-t border-default flex items-center gap-1.5 flex-wrap">
            <span class="text-[10px] font-bold text-subtle uppercase tracking-wide mr-1">Filtros</span>
            <span v-for="c in criteriosAplicados" :key="c"
              class="text-[11px] font-medium text-body bg-slate-100 dark:bg-slate-700/60 px-2 py-0.5 rounded-md">{{ c }}</span>
            <button class="ml-1 text-[11px] font-semibold text-muted hover:text-[#2447F9] flex items-center gap-1" @click="limpiar"><X :size="11" /> Quitar todos</button>
          </div>
        </div>

        <p class="flex items-center gap-1.5 text-[11px] text-muted shrink-0">
          <Info :size="12" class="shrink-0" /> «Enviar» es una vista previa: el envío real de correos y WhatsApp aún no está conectado a un proveedor.
        </p>

        <div v-if="error" class="rounded-lg bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-[12px] font-semibold px-4 py-3 shrink-0">
          {{ error }}
        </div>

        <div class="surface-card rounded-xl shadow-sm overflow-hidden flex-1 min-h-0 flex flex-col">
          <div class="overflow-auto flex-1 min-h-0">
            <table class="w-full text-[12px]">
              <thead class="sticky top-0 z-10 bg-white dark:bg-slate-800">
                <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
                  <th class="px-3 py-2.5 w-8"><input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9]" :checked="todoSel" :disabled="cargando" @change="toggleTodo" /></th>
                  <th class="px-3 py-2.5 font-semibold">Persona</th>
                  <th class="px-3 py-2.5 font-semibold">Ubicación</th>
                  <th class="px-3 py-2.5 font-semibold">Plan</th>
                  <th class="px-3 py-2.5 font-semibold">Último servicio</th>
                  <th class="px-3 py-2.5 font-semibold">Uso</th>
                  <th class="px-3 py-2.5 font-semibold">Contacto</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="cargando">
                  <td colspan="7" class="px-3 py-12 text-center text-[12px] text-muted">
                    <span class="inline-flex items-center gap-2"><Loader2 :size="14" class="animate-spin" /> Consultando audiencia…</span>
                  </td>
                </tr>
                <template v-else>
                  <tr v-for="a in filtrados" :key="a.id"
                    class="border-b border-slate-100 dark:border-slate-800 cursor-pointer align-top transition-colors"
                    :class="sel.has(a.id) ? 'hover:bg-slate-50 dark:hover:bg-slate-800/50' : 'bg-slate-50/60 dark:bg-slate-900/30 opacity-60'"
                    @click="toggleRow(a.id)"
                  >
                    <td class="px-3 py-3" @click.stop>
                      <input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9]" :checked="sel.has(a.id)" @change="toggleRow(a.id)" />
                    </td>
                    <td class="px-3 py-3 min-w-[180px]">
                      <div class="font-semibold text-heading">{{ a.nombre }}</div>
                      <div class="text-[11px] text-muted tabular-nums mt-0.5">
                        CC {{ formatearDocumento(a.documento) }}<template v-if="detallePersona(a)"> · {{ detallePersona(a) }}</template>
                      </div>
                    </td>
                    <td class="px-3 py-3 min-w-[130px]">
                      <div class="text-body">{{ a.direccion }}</div>
                      <div v-if="a.empresa" class="text-[11px] text-muted mt-0.5 truncate max-w-[200px]" :title="a.empresa">{{ a.empresa }}</div>
                    </td>
                    <td class="px-3 py-3 min-w-[120px]">
                      <div class="font-semibold text-[#1E3A8A] dark:text-blue-300">{{ a.plan }}</div>
                      <div class="text-[11px] text-muted mt-0.5">{{ a.vinculacion }}</div>
                    </td>
                    <td class="px-3 py-3 min-w-[150px] max-w-[220px]">
                      <div class="text-body truncate" :title="a.servicio || ''">{{ a.servicio || '—' }}</div>
                      <div v-if="a.concepto || a.especialidad" class="text-[11px] text-muted mt-0.5 truncate" :title="[a.concepto, a.especialidad].filter(Boolean).join(' · ')">
                        {{ [a.concepto, a.especialidad].filter(Boolean).join(' · ') }}
                      </div>
                    </td>
                    <td class="px-3 py-3 whitespace-nowrap">
                      <div class="font-semibold" :class="ultimoUsoCls(a.ultimoUsoDias)">{{ ultimoUsoTxt(a.ultimoUsoDias) }}</div>
                      <div class="text-[11px] text-muted mt-0.5 tabular-nums">{{ a.nServicios }} servicio(s)</div>
                    </td>
                    <td class="px-3 py-3 min-w-[160px]">
                      <div class="flex items-center gap-1.5" :class="a.tieneCorreo ? 'text-body' : 'text-slate-400 dark:text-slate-600'">
                        <Mail :size="12" class="shrink-0" :class="a.tieneCorreo ? 'text-[#2447F9]' : ''" />
                        <span class="truncate max-w-[170px]" :title="a.correo || ''">{{ a.correo || 'Sin correo' }}</span>
                      </div>
                      <div class="flex items-center gap-1.5 mt-0.5" :class="a.tieneCelular ? 'text-body' : 'text-slate-400 dark:text-slate-600'">
                        <Phone :size="12" class="shrink-0" :class="a.tieneCelular ? 'text-[#059669]' : ''" />
                        <span class="tabular-nums">{{ a.telefono || 'Sin celular' }}</span>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="!filtrados.length">
                    <td colspan="7" class="px-3 py-12 text-center text-[12px] text-muted">
                      {{ nFiltros ? 'Ninguna persona coincide con los filtros.' : 'Elija filtros a la izquierda y pulse «Aplicar» para cargar la audiencia.' }}
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <div class="px-4 py-2 border-t border-default flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted">
            <span>
              Mostrando {{ total ? `${nf.format(rangoDesde)}–${nf.format(rangoHasta)}` : '0' }} de {{ nf.format(total) }}
            </span>
            <span>
              De las seleccionadas: <strong class="text-heading tabular-nums">{{ nf.format(conCorreo) }}</strong> con correo ·
              <strong class="text-heading tabular-nums">{{ nf.format(conCelular) }}</strong> con celular
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Fuera de las columnas: si fuera parte de la columna derecha, la
    izquierda se estira de mas para igualar esa altura extra (ver items-stretch). -->
    <div v-if="total > 0" class="flex items-center justify-center gap-3 px-1">
      <button @click="paginaAnterior" :disabled="cargando || cargandoBloque || pagina <= 1"
        class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 text-body flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        title="Página anterior">
        <ChevronLeft :size="15" />
      </button>
      <span class="text-[11px] text-muted">Página <strong class="text-heading">{{ pagina }}</strong> de <strong class="text-heading">{{ totalPaginas }}</strong></span>
      <button @click="paginaSiguiente" :disabled="cargando || cargandoBloque || pagina >= totalPaginas"
        class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 text-body flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        title="Página siguiente">
        <ChevronRight :size="15" />
      </button>
    </div>

    <EnviarSegmentoDialog v-model:visible="enviarVisible" :total="seleccion.length" />
    <AgregarAGrupoDialog v-model:visible="agregarGrupoVisible" :personas="personasParaGrupo" />

    <div v-if="guardarVisible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div class="surface-card rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 border-b border-default surface-header">
          <h3 class="text-[14px] font-bold text-heading">Guardar segmento</h3>
          <button @click="guardarVisible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
        </div>
        <div class="p-5 space-y-3">
          <div v-if="guardado" class="rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-[12px] font-semibold px-4 py-3 flex items-center gap-2">
            <Check :size="15" /> Segmento guardado. Aparece en "Segmentos guardados".
          </div>
          <template v-else>
            <p class="text-[11px] text-muted">
              Se guardará con los <strong class="text-heading">{{ nFiltros }}</strong> filtro(s) aplicados y
              <strong class="text-heading">{{ seleccion.length }}</strong> personas.
            </p>
            <input
              v-model="nombreSegmento"
              placeholder="Nombre del segmento"
              class="w-full h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]"
              @keydown.enter="confirmarGuardar"
            />
          </template>
        </div>
        <div v-if="!guardado" class="flex items-center justify-end gap-2 px-5 py-4 border-t border-default surface-header">
          <button @click="guardarVisible = false" class="h-9 px-5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">Cancelar</button>
          <button
            @click="confirmarGuardar"
            :disabled="!nombreSegmento.trim()"
            class="h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50"
          >Guardar</button>
        </div>
      </div>
    </div>
  </div>
</template>
