<script setup lang="ts">
import { computed, onActivated, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight, ChevronLeft, RefreshCw, SlidersHorizontal, PanelLeftOpen, Send, X, Mail, Phone, Bookmark, Check, Loader2, AlertTriangle } from 'lucide-vue-next'
import { clonarFiltro, resumirFiltros } from '../constants/ciclo-afiliado.constants'
import { getSegmentoPreseleccionado } from '../composables/useSegmentoPreseleccionado'
import { useSegmentosGuardados } from '../composables/useSegmentosGuardados'
import { useSegmentador } from '../composables/useSegmentador'
import FiltrosSegmento from '../components/FiltrosSegmento.vue'
import EnviarSegmentoDialog from '../components/EnviarSegmentoDialog.vue'
import UsoPlanPanel from '../components/UsoPlanPanel.vue'

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
const planStyle = (_p: string) => 'text-[#1E3A8A] dark:text-blue-300'

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
        Arma una audiencia con filtros de Plan Liga (o no Plan Liga) y actúa sobre ella por correo o WhatsApp.
      </p>
    </div>

    <!-- Solo cuando el filtro APLICADO (fApp, no el borrador f) es "Plan Liga": el
    resumen/buscador es especifico de esa audiencia, no tiene sentido con "No plan
    Liga" ni sin filtro de plan elegido. -->
    <UsoPlanPanel v-if="fApp.planLiga === 'Plan Liga'" />

    <button
      class="lg:hidden flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-bold text-body"
      @click="mostrarFiltros = !mostrarFiltros"
    >
      <SlidersHorizontal :size="13" /> Filtros de segmento
      <span v-if="nFiltros" class="bg-[#2447F9] text-white text-[9px] font-bold px-1.5 rounded-full">{{ nFiltros }}</span>
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
        <div class="surface-card rounded-xl shadow-sm px-4 py-3 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div class="flex items-center gap-3 flex-wrap">
            <button
              v-if="filtrosColapsados"
              type="button"
              class="hidden lg:inline-flex items-center gap-1.5 h-8 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-bold text-body hover:border-[#2447F9] hover:text-[#2447F9] transition-all"
              title="Mostrar filtros"
              @click="filtrosColapsados = false"
            >
              <PanelLeftOpen :size="13" /> Filtros
              <span v-if="nFiltros" class="bg-[#2447F9] text-white text-[9px] font-bold px-1.5 rounded-full">{{ nFiltros }}</span>
            </button>
            <span class="text-[15px] font-extrabold text-heading flex items-center gap-2">
              <Loader2 v-if="cargando" :size="16" class="animate-spin text-[#2447F9]" />
              <template v-if="total">{{ nf.format(rangoDesde) }}–{{ nf.format(rangoHasta) }}</template>
              <template v-else>0</template>
              <span class="text-[12px] text-muted font-semibold">/ {{ nf.format(total) }} personas</span>
            </span>
            <span v-if="cargandoBloque" class="flex items-center gap-1.5 text-[11px] font-semibold text-[#2447F9]">
              <Loader2 :size="12" class="animate-spin" /> cargando más…
            </span>
            <span class="text-[11px] text-muted"><strong class="text-heading">{{ seleccion.length }}</strong> seleccionados</span>
            <template v-if="nFiltros">
              <span class="text-[10px] font-bold text-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40 px-2 py-0.5 rounded-full">{{ nFiltros }} filtro(s)</span>
              <button class="text-[10px] font-bold text-muted hover:text-[#2447F9] flex items-center gap-1" @click="limpiar"><X :size="11" /> quitar</button>
            </template>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="abrirGuardar"
              :disabled="!seleccion.length || cargando"
              class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all disabled:opacity-50"
            ><Bookmark :size="13" /> Guardar segmento</button>
            <button
              @click="enviarVisible = true"
              :disabled="!seleccion.length || cargando"
              title="El envío real de correos/WhatsApp desde este módulo todavía no está conectado."
              class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50"
            ><Send :size="13" /> Enviar al segmento</button>
          </div>
        </div>

        <div class="flex items-center gap-1.5 text-[10px] text-amber-600 dark:text-amber-400 font-semibold shrink-0">
          <AlertTriangle :size="12" /> El envío de correos y WhatsApp desde Audiencias todavía no está conectado a un proveedor real — por ahora es solo una vista previa.
        </div>

        <div v-if="error" class="rounded-xl bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-[12px] font-semibold px-4 py-3 shrink-0">
          {{ error }}
        </div>

        <div class="surface-card rounded-xl shadow-sm overflow-hidden flex-1 min-h-0 flex flex-col">
          <div class="overflow-auto flex-1 min-h-0">
            <table class="w-full text-[12px]">
              <thead>
                <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
                  <th class="px-3 py-2.5 w-8"><input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9]" :checked="todoSel" :disabled="cargando" @change="toggleTodo" /></th>
                  <th class="px-3 py-2.5 font-semibold">Persona</th>
                  <th class="px-3 py-2.5 font-semibold">Sexo</th>
                  <th class="px-3 py-2.5 font-semibold">Edad</th>
                  <th class="px-3 py-2.5 font-semibold">Empresa</th>
                  <th class="px-3 py-2.5 font-semibold">Dirección</th>
                  <th class="px-3 py-2.5 font-semibold">Plan</th>
                  <th class="px-3 py-2.5 font-semibold">Concepto</th>
                  <th class="px-3 py-2.5 font-semibold">Servicio</th>
                  <th class="px-3 py-2.5 font-semibold">Especialidad</th>
                  <th class="px-3 py-2.5 font-semibold">Último uso</th>
                  <th class="px-3 py-2.5 font-semibold">Serv.</th>
                  <th class="px-3 py-2.5 font-semibold">Correo</th>
                  <th class="px-3 py-2.5 font-semibold">Teléfono</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="cargando">
                  <td colspan="14" class="px-3 py-12 text-center text-[12px] text-muted">
                    <span class="inline-flex items-center gap-2"><Loader2 :size="14" class="animate-spin" /> Consultando audiencia…</span>
                  </td>
                </tr>
                <template v-else>
                  <tr v-for="a in filtrados" :key="a.id"
                    class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer"
                    :class="sel.has(a.id) ? '' : 'opacity-55'"
                    @click="toggleRow(a.id)"
                  >
                    <td class="px-3 py-2.5" @click.stop>
                      <input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9]" :checked="sel.has(a.id)" @change="toggleRow(a.id)" />
                    </td>
                    <td class="px-3 py-2.5">
                      <div class="font-bold text-heading">{{ a.nombre }}</div>
                      <div class="text-[11px] font-semibold text-[#2447F9] dark:text-blue-300 tabular-nums">CC {{ formatearDocumento(a.documento) }}</div>
                    </td>
                    <td class="px-3 py-2.5 text-body">{{ a.sexo || '—' }}</td>
                    <td class="px-3 py-2.5 text-body tabular-nums">{{ a.edad ?? '—' }}</td>
                    <td class="px-3 py-2.5 text-body">{{ a.empresa || '—' }}</td>
                    <td class="px-3 py-2.5 text-body">{{ a.direccion }}</td>
                    <td class="px-3 py-2.5">
                      <span class="text-[10px] font-bold" :class="planStyle(a.plan)">{{ a.plan }}</span>
                      <span class="text-[10px] text-muted"> · {{ a.vinculacion }}</span>
                    </td>
                    <td class="px-3 py-2.5 text-body max-w-[180px]">
                      <span class="block truncate" :title="a.concepto || ''">{{ a.concepto || '—' }}</span>
                    </td>
                    <td class="px-3 py-2.5 text-body max-w-[180px]">
                      <span class="block truncate" :title="a.servicio || ''">{{ a.servicio || '—' }}</span>
                    </td>
                    <td class="px-3 py-2.5 text-body max-w-[160px]">
                      <span class="block truncate" :title="a.especialidad || ''">{{ a.especialidad || '—' }}</span>
                    </td>
                    <td class="px-3 py-2.5 font-semibold" :class="ultimoUsoCls(a.ultimoUsoDias)">{{ ultimoUsoTxt(a.ultimoUsoDias) }}</td>
                    <td class="px-3 py-2.5 text-body tabular-nums">{{ a.nServicios }}</td>
                    <td class="px-3 py-2.5">
                      <span class="inline-flex items-center gap-1.5">
                        <Mail :size="12" :class="a.tieneCorreo ? 'text-[#2447F9]' : 'text-slate-300 dark:text-slate-600'" />
                        {{ a.correo || '—' }}
                      </span>
                    </td>
                    <td class="px-3 py-2.5">
                      <span class="inline-flex items-center gap-1.5">
                        <Phone :size="12" :class="a.tieneCelular ? 'text-[#059669]' : 'text-slate-300 dark:text-slate-600'" />
                        {{ a.telefono || '—' }}
                      </span>
                    </td>
                  </tr>
                  <tr v-if="!filtrados.length">
                    <td colspan="14" class="px-3 py-12 text-center text-[12px] text-muted">
                      {{ nFiltros ? 'Ninguna persona coincide con los filtros.' : 'Aplica filtros para cargar la audiencia.' }}
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
          <div class="px-3 py-2 border-t border-default text-[10px] text-muted">
            {{ seleccion.length }} seleccionados · <span class="text-heading font-semibold">{{ conCorreo }}</span> con correo · <span class="text-heading font-semibold">{{ conCelular }}</span> con celular
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
