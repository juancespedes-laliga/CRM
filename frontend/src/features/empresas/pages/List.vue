<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Plus, Download, Upload, Loader2, X, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { Empresa, EmpresaDraft } from '../types/empresa'
import { EMPRESA_DRAFT_VACIO } from '../constants/empresas.constants'
import { useEmpresas } from '../composables/useEmpresas'
import { exportarEmpresasExcel } from '../utils/exportarEmpresasExcel'
import EmpresaFormDialog from '../dialogs/EmpresaFormDialog.vue'
import HistorialDrawer from '../dialogs/HistorialDrawer.vue'
import SeguimientoDialog from '../dialogs/SeguimientoDialog.vue'
import EmpresasTable from '../tables/EmpresasTable.vue'
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'

const { gestionar: puedeGestionar, eliminar: puedeEliminar } = permisosDeModulo('empresas')

const {
  empresas, cargandoEmpresas, errorEmpresas, cargarEmpresas,
  buscar, filtroEstado, filtroIndustria,
  empresasFiltradas, industrias,
  paginaActual, totalPaginas, hayPaginaAnterior, hayPaginaSiguiente,
  empresasPaginadas, paginaSiguiente, paginaAnterior,
  crearEmpresa, actualizarEmpresa, guardandoEmpresa, errorGuardarEmpresa,
  eliminarEmpresa, errorEliminarEmpresa,
  historialActual, cargandoHistorial, cargarHistorial,
  importarDesdePlanLiga, importandoPlanLiga, errorImportarPlanLiga, resultadoImportarPlanLiga,
} = useEmpresas()

onMounted(() => { cargarEmpresas() })

const modalVisible = ref(false)
const modalModo = ref<'nuevo' | 'editar'>('nuevo')
const empresaEditando = ref<Empresa | null>(null)
const draft = ref<EmpresaDraft>({ ...EMPRESA_DRAFT_VACIO })

const abrirNuevo = () => {
  modalModo.value = 'nuevo'
  empresaEditando.value = null
  errorGuardarEmpresa.value = null
  draft.value = { ...EMPRESA_DRAFT_VACIO }
  modalVisible.value = true
}
const abrirEditar = (e: Empresa) => {
  modalModo.value = 'editar'
  empresaEditando.value = e
  errorGuardarEmpresa.value = null
  draft.value = { razonSocial: e.razonSocial, nit: e.nit, industria: e.industria, direccion: e.direccion, ciudad: e.ciudad, estado: e.estado }
  modalVisible.value = true
}
const guardar = async () => {
  if (modalModo.value === 'nuevo') {
    const ok = await crearEmpresa(draft.value)
    if (ok) modalVisible.value = false
  } else if (empresaEditando.value) {
    const ok = await actualizarEmpresa(empresaEditando.value.id, draft.value)
    if (ok) modalVisible.value = false
  }
}

const confirmBorrarVisible = ref(false)
const empresaABorrar = ref<Empresa | null>(null)
const pedirBorrarEmpresa = (e: Empresa) => {
  empresaABorrar.value = e
  errorEliminarEmpresa.value = null
  confirmBorrarVisible.value = true
}
const confirmarBorrado = async () => {
  if (empresaABorrar.value) await eliminarEmpresa(empresaABorrar.value.id)
  empresaABorrar.value = null
}

const drawerVisible = ref(false)
const empresaHistorial = ref<Empresa | null>(null)
const abrirHistorial = (e: Empresa) => { empresaHistorial.value = e; drawerVisible.value = true; cargarHistorial(e) }

// ─── Registrar actividad (desde el drawer de historial) ────────────────────
const modalSegVisible = ref(false)
const abrirSeguimiento = () => { modalSegVisible.value = true }
const alRegistrarActividad = () => { if (empresaHistorial.value) cargarHistorial(empresaHistorial.value) }

const exportar = () => exportarEmpresasExcel(
  empresasFiltradas.value,
  buscar.value,
  filtroEstado.value,
  filtroIndustria.value,
)
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-[18px] font-bold text-[#0F172A] dark:text-slate-100 flex items-center gap-2">
          Gestión de Empresas
          <span class="bg-[#EEF2FF] dark:bg-blue-950/50 text-slate-900 dark:text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full">{{ empresas.length }}</span>
        </h2>
        <p class="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">Empresas vinculadas e industrias</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="puedeGestionar"
          @click="importarDesdePlanLiga"
          :disabled="importandoPlanLiga"
          class="flex items-center gap-1.5 h-9 px-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
          title="Crea una empresa por cada nombre distinto en intranet_planliga.empresa que todavía no exista en este catálogo"
        >
          <Loader2 v-if="importandoPlanLiga" :size="13" class="animate-spin" />
          <Upload v-else :size="13" />
          Importar de Plan Liga
        </button>
        <button @click="exportar" class="flex items-center gap-1.5 h-9 px-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
          <Download :size="13" /> Exportar
        </button>
        <button v-if="puedeGestionar" @click="abrirNuevo" class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all">
          <Plus :size="14" /> Nueva empresa
        </button>
      </div>
    </div>

    <div v-if="resultadoImportarPlanLiga" class="flex items-center gap-2.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl px-4 py-3">
      <p class="text-[12px] font-semibold text-emerald-700 dark:text-emerald-300">{{ resultadoImportarPlanLiga }}</p>
      <button @click="resultadoImportarPlanLiga = null" class="ml-auto text-emerald-400 hover:text-emerald-600 dark:hover:text-emerald-300 shrink-0"><X :size="13" /></button>
    </div>
    <div v-if="errorImportarPlanLiga" class="flex items-center gap-2.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-4 py-3">
      <p class="text-[12px] font-semibold text-red-600 dark:text-red-400">{{ errorImportarPlanLiga }}</p>
      <button @click="errorImportarPlanLiga = null" class="ml-auto text-red-400 hover:text-red-600 dark:hover:text-red-300 shrink-0"><X :size="13" /></button>
    </div>

    <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm px-4 py-3">
      <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
        <div class="relative flex-1 min-w-0">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
          <input v-model="buscar" placeholder="Buscar por razón social, NIT o ciudad..." class="w-full h-9 pl-9 pr-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] text-slate-900 dark:text-slate-100 outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
        <div class="flex items-center gap-2">
          <select v-model="filtroEstado" class="h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todos">Estado: Todos</option>
            <option value="Activa">Activa</option>
            <option value="Inactiva">Inactiva</option>
          </select>
          <select v-model="filtroIndustria" class="h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todas">Industria: Todas</option>
            <option v-for="ind in industrias" :key="ind" :value="ind">{{ ind }}</option>
          </select>
        </div>
      </div>
      <div class="mt-2 text-[11px] text-slate-400 dark:text-slate-500">
        <template v-if="cargandoEmpresas">Cargando empresas...</template>
        <template v-else>
          Mostrando <strong class="text-slate-600 dark:text-slate-300">{{ empresasFiltradas.length }}</strong> empresas
        </template>
      </div>
      <p v-if="errorEmpresas" class="mt-1 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorEmpresas }}</p>
      <p v-if="errorEliminarEmpresa" class="mt-1 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorEliminarEmpresa }}</p>
    </div>

    <EmpresasTable
      :rows="empresasPaginadas"
      :puede-gestionar="puedeGestionar"
      :puede-eliminar="puedeEliminar"
      @editar="abrirEditar"
      @historial="abrirHistorial"
      @borrar="pedirBorrarEmpresa"
    />

    <div v-if="empresasFiltradas.length > 0" class="flex items-center justify-center gap-3 px-1">
      <button @click="paginaAnterior" :disabled="!hayPaginaAnterior"
        class="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        title="Página anterior">
        <ChevronLeft :size="15" />
      </button>
      <span class="text-[11px] text-slate-400 dark:text-slate-500">Página <strong class="text-slate-600 dark:text-slate-300">{{ paginaActual }}</strong> de <strong class="text-slate-600 dark:text-slate-300">{{ totalPaginas }}</strong></span>
      <button @click="paginaSiguiente" :disabled="!hayPaginaSiguiente"
        class="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        title="Página siguiente">
        <ChevronRight :size="15" />
      </button>
    </div>

    <EmpresaFormDialog
      v-model:visible="modalVisible"
      v-model:draft="draft"
      :modo="modalModo"
      :guardando="guardandoEmpresa"
      :error="errorGuardarEmpresa"
      @submit="guardar"
    />

    <HistorialDrawer
      v-model:visible="drawerVisible"
      :empresa="empresaHistorial"
      :items="historialActual"
      :cargando="cargandoHistorial"
      @registrar="abrirSeguimiento"
    />

    <SeguimientoDialog
      v-model:visible="modalSegVisible"
      :empresa="empresaHistorial"
      @registrado="alRegistrarActividad"
    />

    <ConfirmDialog
      v-model:visible="confirmBorrarVisible"
      titulo="Eliminar empresa"
      :mensaje="`¿Eliminar a ${empresaABorrar?.razonSocial}? Esta acción no se puede deshacer.`"
      @confirmar="confirmarBorrado"
    />
  </div>
</template>
