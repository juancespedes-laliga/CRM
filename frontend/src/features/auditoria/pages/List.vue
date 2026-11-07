<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Search, Download, X, ChevronRight, Loader2, Heart, UserRound, ArrowLeft, ListChecks, Users, ArrowLeftRight, RefreshCw, Layers,
  CheckCircle2, XCircle, CalendarClock, CalendarX,
} from 'lucide-vue-next'
import type {
  ModuloSeleccion, ObjetivoHistorial, RegistroCambio, RenovacionRegistro, TabAuditoria, TarjetaResumen,
} from '../types/auditoria'
import {
  ACCION_LABEL, DIAS_POR_VENCER, MODULO_POR_KEY, ORIGEN_LABEL, POR_PAGINA, VISTA_POR_KEY,
  esModuloValido, etiquetaModulo, incluyePlanLiga,
} from '../constants/auditoria.constants'
import { useCambiosAuditoria } from '../composables/useCambiosAuditoria'
import { useRenovacionesAuditoria } from '../composables/useRenovacionesAuditoria'
import { exportarCambiosExcel } from '../utils/exportarAuditoriaExcel'
// Mismo resumen que muestran las tarjetas de Titulares y Beneficiarios.
import { exportarTitulares, getResumenTitulares } from '@/features/plan-liga/services/plan-liga.api'
import AuditoriaTabs from '../components/AuditoriaTabs.vue'
import ResumenCards from '../components/ResumenCards.vue'
import Paginador from '../components/Paginador.vue'
import CambiosTable from '../tables/CambiosTable.vue'
import RenovacionesTable from '../tables/RenovacionesTable.vue'
import DetalleCambioDrawer from '../dialogs/DetalleCambioDrawer.vue'
import HistorialDrawer from '../dialogs/HistorialDrawer.vue'

const route = useRoute()
const router = useRouter()

// ── Módulo y pestaña ─────────────────────────────────────────────
// El módulo viene de la ruta (/auditoria/titulares). Cada módulo es su propia
// instancia de esta página (el keep-alive del layout usa la ruta como key),
// así que aquí no cambia; para elegir otro se vuelve a /auditoria.
// Un módulo inválido en la URL lo devuelve la guarda de la ruta (routes.ts).
const modulo = ref<ModuloSeleccion>(esModuloValido(route.params.modulo) ? route.params.modulo : 'todos')
const infoModulo = computed(() => (modulo.value === 'todos' ? null : VISTA_POR_KEY[modulo.value]))
const tab = ref<TabAuditoria>(route.query.tab === 'renovaciones' ? 'renovaciones' : 'cambios')

const renovacionesDisponible = computed(() => incluyePlanLiga(modulo.value))

watch(renovacionesDisponible, (ok) => { if (!ok) tab.value = 'cambios' }, { immediate: true })

// La pestaña queda en la URL (?tab=renovaciones) para poder compartir el enlace.
watch(tab, () => {
  router.replace({ query: { ...route.query, tab: tab.value === 'cambios' ? undefined : tab.value } })
})

// ── Registro de cambios ──────────────────────────────────────────
const C = useCambiosAuditoria(modulo)
const filtrosC = C.filtros

const tarjetasCambios = computed<TarjetaResumen[]>(() => {
  const r = C.resumen.value
  const t: TarjetaResumen[] = [
    { key: 'total', label: 'Total de acciones', valor: r.total, icono: ListChecks },
    { key: 'usuarios', label: 'Usuarios', valor: r.usuarios, icono: Users, ayuda: 'que hicieron cambios' },
    { key: 'estado', label: 'Cambios de estado', valor: r.cambiosEstado, icono: ArrowLeftRight },
  ]
  if (C.muestraPlanLiga.value) t.push({ key: 'renov', label: 'Renovaciones', valor: r.renovaciones, icono: RefreshCw })
  t.push({ key: 'masivos', label: 'Cambios masivos', valor: r.masivos, icono: Layers, ayuda: 'Excel o por grupo' })
  return t
})

// ── Renovaciones ─────────────────────────────────────────────────
const R = useRenovacionesAuditoria()
const filtrosR = R.filtros

const tarjetasRenovaciones = computed<TarjetaResumen[]>(() => {
  const r = R.resumen.value
  return [
    { key: 'renovados', label: 'Renovados', valor: r.renovados, icono: CheckCircle2, claseValor: 'text-emerald-600 dark:text-emerald-400' },
    { key: 'sinRenovar', label: 'Sin renovar', valor: r.sinRenovar, icono: XCircle },
    { key: 'porVencer', label: 'Por vencer', valor: r.porVencer, icono: CalendarClock, claseValor: 'text-amber-600 dark:text-amber-400', ayuda: `${DIAS_POR_VENCER} días o menos` },
    { key: 'vencidos', label: 'Vencidos', valor: r.vencidos, icono: CalendarX, claseValor: 'text-red-600 dark:text-red-400' },
  ]
})

// Totales de activos (los mismos de la pantalla Titulares y Beneficiarios).
const totalTitularesActivos = ref<number | null>(null)
const totalBeneficiariosActivos = ref<number | null>(null)
const errorTotalesPlanLiga = ref<string | null>(null)
async function cargarTotalesPlanLiga() {
  errorTotalesPlanLiga.value = null
  try {
    const data = await getResumenTitulares()
    totalTitularesActivos.value = data.titulares_activos
    totalBeneficiariosActivos.value = data.beneficiarios_activos
  } catch (e) {
    errorTotalesPlanLiga.value = e instanceof Error ? e.message : 'No se pudo cargar el total de titulares y beneficiarios.'
  }
}

// Las renovaciones (y los totales) se cargan la primera vez que se abre la pestaña.
watch(tab, (t) => {
  if (t !== 'renovaciones') return
  if (R.registros.value.length === 0 && !R.cargando.value) R.cargar()
  if (totalTitularesActivos.value === null) cargarTotalesPlanLiga()
}, { immediate: true })

onMounted(() => {
  C.cargar()
})

// ── Detalle e historial ──────────────────────────────────────────
const detalleVisible = ref(false)
const detalleId = ref<number | null>(null)
const historialVisible = ref(false)
const historialObjetivo = ref<ObjetivoHistorial | null>(null)

const abrirDetalle = (c: RegistroCambio) => {
  historialVisible.value = false
  detalleId.value = c.id
  detalleVisible.value = true
}
const abrirHistorialDeCambio = (c: RegistroCambio) => {
  detalleVisible.value = false
  historialObjetivo.value = { modulo: c.modulo, registroId: c.registroId, nombre: c.registroNombre, documento: c.documento }
  historialVisible.value = true
}
const abrirHistorialDeRenovacion = (r: RenovacionRegistro) => {
  historialObjetivo.value = {
    modulo: r.tipo === 'titular' ? 'titulares' : 'beneficiarios',
    registroId: r.id, nombre: r.nombre, documento: r.documento,
  }
  historialVisible.value = true
}

// ── Exportar ─────────────────────────────────────────────────────
// Mismo flujo que el Exportar de Titulares y Beneficiarios: botón con
// "Exportando..." y aviso mientras se genera el archivo.
const exportando = ref(false)
const errorExportar = ref<string | null>(null)
const exportar = async () => {
  exportando.value = true
  errorExportar.value = null
  // Deja pintar el aviso antes de armar el archivo (puede tardar con muchas filas).
  await new Promise(res => setTimeout(res, 50))
  try {
    if (tab.value === 'cambios') {
      // Registro de cambios: Excel propio de auditoría (quién, qué, antes → después).
      exportarCambiosExcel(C.filtrados.value, modulo.value)
    } else {
      // Renovaciones: el mismo Excel de titulares y beneficiarios que genera la
      // pantalla Titulares y Beneficiarios (lo arma el backend), con la búsqueda
      // y el estado de aquí.
      const estado = filtrosR.estado === 'Activo' || filtrosR.estado === 'Inactivo' ? filtrosR.estado : undefined
      const blob = await exportarTitulares({ busqueda: filtrosR.buscar.trim() || undefined, estado })
      const url = URL.createObjectURL(blob)
      const enlace = document.createElement('a')
      enlace.href = url
      enlace.download = `titulares_beneficiarios_${new Date().toISOString().split('T')[0]}.xlsx`
      enlace.click()
      URL.revokeObjectURL(url)
    }
  } catch (e) {
    errorExportar.value = e instanceof Error ? e.message : 'No se pudo exportar el listado.'
  } finally {
    exportando.value = false
  }
}
// En Renovaciones el Excel lo arma el backend con todos los titulares/beneficiarios que coincidan.
const totalExportable = computed(() => (tab.value === 'cambios' ? C.filtrados.value.length : null))

const subtitulo = computed(() => {
  if (modulo.value === 'todos') return 'Todo lo que se hace en el CRM, en todos los módulos'
  if (modulo.value === 'plan-liga') return 'Cambios y renovaciones de titulares y beneficiarios de Plan Liga'
  return `Cambios realizados en ${VISTA_POR_KEY[modulo.value].label}`
})

const select = 'h-9 px-3 rounded-lg input-surface text-[11px] font-medium text-body outline-none cursor-pointer'
const inputFecha = 'h-9 px-2.5 rounded-lg input-surface text-[11px] font-medium text-body outline-none'
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <!-- Encabezado + breadcrumb (volver a elegir módulo) -->
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
      <div>
        <nav class="flex items-center gap-1.5 text-[12px] mb-1.5">
          <button type="button" @click="router.push('/auditoria')" class="text-slate-400 dark:text-slate-500 hover:text-[#2447F9] dark:hover:text-blue-400 transition-colors">Auditoría</button>
          <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
          <span class="font-bold text-[#0F172A] dark:text-slate-100">{{ etiquetaModulo(modulo) }}</span>
        </nav>
        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="router.push('/auditoria')"
            class="w-8 h-8 rounded-lg border border-default surface-card flex items-center justify-center text-slate-500 dark:text-slate-400 surface-hover transition-all"
            title="Elegir otro módulo"
            aria-label="Elegir otro módulo"
          >
            <ArrowLeft :size="14" />
          </button>
          <div v-if="infoModulo" class="w-8 h-8 rounded-lg flex items-center justify-center" :style="{ backgroundColor: infoModulo.bg }">
            <component :is="infoModulo.icono" :size="16" :style="{ color: infoModulo.color }" />
          </div>
          <h2 class="text-[18px] font-bold text-heading">Auditoría de {{ etiquetaModulo(modulo).toLowerCase() }}</h2>
        </div>
        <p class="text-[12px] text-muted mt-1">{{ subtitulo }}</p>
        <p v-if="errorExportar" class="text-[11px] text-red-600 dark:text-red-400 mt-1">{{ errorExportar }}</p>
      </div>
      <button
        @click="exportar"
        :disabled="exportando || totalExportable === 0"
        class="flex items-center gap-1.5 h-9 px-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all self-start sm:self-auto"
      >
        <Loader2 v-if="exportando" :size="13" class="animate-spin" />
        <Download v-else :size="13" />
        {{ exportando ? 'Exportando...' : totalExportable === null ? 'Exportar' : `Exportar (${totalExportable.toLocaleString('es-CO')})` }}
      </button>
    </div>

    <div v-if="exportando" class="flex items-center gap-2.5 bg-[#EEF2FF] dark:bg-blue-950/40 border border-[#C7D2FE] dark:border-blue-800 rounded-xl px-4 py-3">
      <Loader2 :size="16" class="animate-spin text-[#2447F9] dark:text-blue-400 shrink-0" />
      <p class="text-[12px] font-bold text-slate-900 dark:text-white">Generando el archivo, esto puede tardar unos segundos...</p>
    </div>

    <AuditoriaTabs v-model="tab" :renovaciones-disponible="renovacionesDisponible" />

    <!-- ═══════════ Registro de cambios ═══════════ -->
    <template v-if="tab === 'cambios'">
      <ResumenCards :tarjetas="tarjetasCambios" />

      <div class="surface-card rounded-2xl shadow-sm px-4 py-3 space-y-3">
        <div class="relative">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
          <input
            v-model="filtrosC.buscar"
            :placeholder="modulo === 'todos' ? 'Buscar por nombre, documento, ID, usuario o motivo...' : `Buscar en ${etiquetaModulo(modulo)} por nombre, documento, ID, usuario o motivo...`"
            class="w-full h-9 pl-9 pr-4 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <select v-if="C.variosModulos.value" v-model="filtrosC.submodulo" :class="select" aria-label="Módulo">
            <option value="todos">{{ modulo === 'plan-liga' ? 'Tipo: Titulares y beneficiarios' : 'Módulo: Todos' }}</option>
            <option v-for="m in C.submodulosDisponibles.value" :key="m" :value="m">{{ MODULO_POR_KEY[m].label }}</option>
          </select>
          <select v-model="filtrosC.accion" :class="select" aria-label="Acción">
            <option value="todas">Acción: Todas</option>
            <option v-for="a in C.accionesDisponibles.value" :key="a" :value="a">{{ ACCION_LABEL[a] }}</option>
          </select>
          <select v-model="filtrosC.usuario" :class="select" aria-label="Usuario">
            <option value="todos">Usuario: Todos</option>
            <option v-for="u in C.usuarios.value" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.usuario }})</option>
          </select>
          <select v-model="filtrosC.origen" :class="select" aria-label="Origen">
            <option value="todos">Origen: Todos</option>
            <option v-for="(label, key) in ORIGEN_LABEL" :key="key" :value="key">{{ label }}</option>
          </select>
          <select v-model="filtrosC.estado" :class="select" aria-label="Estado resultante">
            <option value="todos">Estado resultante: Todos</option>
            <option v-for="e in C.estados.value" :key="e" :value="e">{{ e }}</option>
          </select>
          <select v-if="C.muestraPlanLiga.value" v-model="filtrosC.renovado" :class="select" aria-label="Renovado">
            <option value="todos">Renovado: Todos</option>
            <option value="si">Renovado</option>
            <option value="no">No renovado</option>
          </select>
          <div class="flex items-center gap-1.5">
            <input type="date" v-model="filtrosC.desde" :max="filtrosC.hasta || undefined" :class="inputFecha" aria-label="Desde" />
            <span class="text-[11px] text-muted">a</span>
            <input type="date" v-model="filtrosC.hasta" :min="filtrosC.desde || undefined" :class="inputFecha" aria-label="Hasta" />
          </div>
          <button v-if="C.hayFiltros.value" type="button" @click="C.limpiarFiltros()" class="flex items-center gap-1 h-9 px-3 rounded-lg text-[11px] font-semibold text-subtle hover:text-heading transition-colors">
            <X :size="12" /> Limpiar
          </button>
        </div>
        <div class="text-[11px] text-muted">
          <template v-if="C.cargando.value">Cargando cambios...</template>
          <template v-else>Mostrando <strong class="text-body">{{ C.filtrados.value.length.toLocaleString('es-CO') }}</strong> cambios</template>
        </div>
        <p v-if="C.error.value" class="text-[11px] font-medium text-red-500 dark:text-red-400">{{ C.error.value }}</p>
        <p v-if="C.truncado.value" class="text-[11px] font-medium text-amber-600 dark:text-amber-400">Se muestran solo los 5.000 cambios más recientes. Usa el rango de fechas para ver los anteriores.</p>
      </div>

      <CambiosTable
        :rows="C.paginados.value"
        :cargando="C.cargando.value"
        :muestra-modulo="C.variosModulos.value"
        :muestra-plan-liga="C.muestraPlanLiga.value"
        @detalle="abrirDetalle"
        @historial="abrirHistorialDeCambio"
      />
      <Paginador v-model="C.pagina.value" :total="C.filtrados.value.length" :por-pagina="POR_PAGINA" />
    </template>

    <!-- ═══════════ Renovaciones ═══════════ -->
    <template v-else>
      <!-- Totales de activos, como en Titulares y Beneficiarios -->
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm p-5">
          <div class="w-9 h-9 rounded-xl bg-[#FCE7F3] dark:bg-pink-950/50 flex items-center justify-center mb-3"><Heart :size="17" class="text-[#EC4899]" /></div>
          <div class="text-[28px] font-bold text-[#0F172A] dark:text-slate-100 leading-none tabular-nums">{{ totalTitularesActivos === null ? '…' : totalTitularesActivos.toLocaleString('es-CO') }}</div>
          <div class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mt-1">Titulares activos</div>
        </div>
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm p-5">
          <div class="w-9 h-9 rounded-xl bg-[#EEF2FF] dark:bg-blue-950/50 flex items-center justify-center mb-3"><UserRound :size="17" class="text-[#2447F9]" /></div>
          <div class="text-[28px] font-bold text-[#0F172A] dark:text-slate-100 leading-none tabular-nums">{{ totalBeneficiariosActivos === null ? '…' : totalBeneficiariosActivos.toLocaleString('es-CO') }}</div>
          <div class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mt-1">Beneficiarios activos</div>
        </div>
      </div>
      <p v-if="errorTotalesPlanLiga" class="-mt-2 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorTotalesPlanLiga }}</p>

      <ResumenCards
        :tarjetas="tarjetasRenovaciones"
        clicables
        :activa="R.tarjetaActiva.value"
        @seleccionar="(k) => R.filtrarPorTarjeta(k as any)"
      />

      <div class="surface-card rounded-2xl shadow-sm px-4 py-3 space-y-2">
        <div class="flex flex-wrap items-center gap-2">
          <!-- Misma búsqueda que en Titulares y Beneficiarios -->
          <div class="relative flex-1 min-w-[220px] max-w-[350px]">
            <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input v-model="filtrosR.buscar" placeholder="(cédula,nombre,empresa)..." title="Buscar por cédula, nombre o empresa"
              class="w-full h-9 pl-9 pr-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all truncate" />
          </div>
          <select v-model="filtrosR.tipo" :class="select" aria-label="Tipo">
            <option value="todos">Tipo: Todos</option>
            <option value="titular">Titulares</option>
            <option value="beneficiario">Beneficiarios</option>
          </select>
          <select v-model="filtrosR.renovado" :class="select" aria-label="Renovado">
            <option value="todos">Renovado: Todos</option>
            <option value="si">Renovado</option>
            <option value="no">No renovado</option>
          </select>
          <select v-model="filtrosR.vigencia" :class="select" aria-label="Vigencia">
            <option value="todas">Vigencia: Todas</option>
            <option value="vigente">Vigente</option>
            <option value="por_vencer">Por vencer</option>
            <option value="vencido">Vencido</option>
          </select>
          <select v-model="filtrosR.estado" :class="select" aria-label="Estado">
            <option value="todos">Estado: Todos</option>
            <option v-for="e in R.estados.value" :key="e" :value="e">{{ e }}</option>
          </select>
          <button v-if="R.hayFiltros.value" type="button" @click="R.limpiarFiltros()" class="flex items-center gap-1 h-9 px-3 rounded-lg text-[11px] font-semibold text-subtle hover:text-heading transition-colors">
            <X :size="12" /> Limpiar
          </button>
        </div>
        <div class="text-[11px] text-muted">
          <template v-if="R.cargando.value">Cargando renovaciones...</template>
          <template v-else>Mostrando <strong class="text-body">{{ R.filtrados.value.length.toLocaleString('es-CO') }}</strong> de <strong class="text-body">{{ R.registros.value.length.toLocaleString('es-CO') }}</strong> personas · primero las más cercanas a vencer</template>
        </div>
        <p v-if="R.error.value" class="text-[11px] font-medium text-red-500 dark:text-red-400">{{ R.error.value }}</p>
      </div>

      <RenovacionesTable
        :rows="R.paginados.value"
        :cargando="R.cargando.value"
        muestra-tipo
        @historial="abrirHistorialDeRenovacion"
      />
      <Paginador v-model="R.pagina.value" :total="R.filtrados.value.length" :por-pagina="POR_PAGINA" />
    </template>

    <DetalleCambioDrawer v-model:visible="detalleVisible" :cambio-id="detalleId" @historial="abrirHistorialDeCambio" />
    <HistorialDrawer v-model:visible="historialVisible" :objetivo="historialObjetivo" @detalle="abrirDetalle" />
  </div>
</template>
