<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Plus, Download, X } from 'lucide-vue-next'
import type { Contacto, ContactoDraft } from '../types/contacto'
import { CONTACTO_DRAFT_VACIO, ESTADO_CONTACTO_OPTIONS, TIPO_CONTACTO_OPTIONS } from '../constants/contactos.constants'
import { useContactos } from '../composables/useContactos'
import { exportarContactosExcel } from '../utils/exportarContactosExcel'
import ContactoFormDialog from '../dialogs/ContactoFormDialog.vue'
import SeguimientoDialog from '../dialogs/SeguimientoDialog.vue'
import HistorialDrawer from '../dialogs/HistorialDrawer.vue'
import ContactosTable from '../tables/ContactosTable.vue'
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'

const { gestionar: puedeGestionar, eliminar: puedeEliminar } = permisosDeModulo('contactos')

const {
  contactos, cargandoContactos, errorContactos, cargarContactos,
  buscar, filtroEstado, filtroTipoContacto, filtroCiudad, filtroDepartamento, filtroResponsable, filtroSexo, filtroEdad,
  contactosFiltrados, ciudades, departamentosLista, responsables, filtrosActivos, limpiarFiltros,
  paginaActual, paginado, totalPaginas,
  crearContacto, actualizarContacto, guardandoContacto, errorGuardarContacto,
  alternarEstadoContacto, cambiandoEstadoId, errorCambiarEstado,
  eliminarContacto, errorEliminarContacto,
  historialActual, cargandoHistorial, cargarHistorial,
  etiquetas, cargandoEtiquetas, cargarEtiquetas,
  crearEtiqueta, creandoEtiqueta, errorCrearEtiqueta,
  empresas, cargandoEmpresas, cargarEmpresas,
} = useContactos()

onMounted(() => { cargarContactos(); cargarEtiquetas(); cargarEmpresas() })

// ─── Modal Contacto ─────────────────────────────────────────────────────────
const modalVisible     = ref(false)
const modalModo        = ref<'nuevo' | 'editar'>('nuevo')
const contactoEditando = ref<Contacto | null>(null)
const draft            = ref<ContactoDraft>({ ...CONTACTO_DRAFT_VACIO })

const abrirNuevo = () => {
  modalModo.value = 'nuevo'
  contactoEditando.value = null
  errorGuardarContacto.value = null
  draft.value = { ...CONTACTO_DRAFT_VACIO, etiquetas: [] }
  modalVisible.value = true
}
const abrirEditar = (c: Contacto) => {
  modalModo.value = 'editar'
  contactoEditando.value = c
  errorGuardarContacto.value = null
  // El draft usa código (ciudadCodigo/departamentoCodigo) porque los Select del formulario
  // trabajan con option-value="codigo"; c.ciudad/c.departamento son el nombre legible de la tabla.
  draft.value = { ...c, ciudad: c.ciudadCodigo, departamento: c.departamentoCodigo, etiquetas: [...c.etiquetas] }
  modalVisible.value = true
}
const guardarContacto = async () => {
  if (modalModo.value === 'nuevo') {
    const ok = await crearContacto(draft.value)
    if (ok) modalVisible.value = false
  } else if (contactoEditando.value) {
    const ok = await actualizarContacto(contactoEditando.value.id, draft.value)
    if (ok) modalVisible.value = false
  }
}

// ─── Eliminar contacto ──────────────────────────────────────────────────────
const confirmBorrarVisible = ref(false)
const contactoABorrar = ref<Contacto | null>(null)
const pedirBorrarContacto = (c: Contacto) => {
  contactoABorrar.value = c
  errorEliminarContacto.value = null
  confirmBorrarVisible.value = true
}
const confirmarBorrado = async () => {
  if (contactoABorrar.value) await eliminarContacto(contactoABorrar.value.id)
  contactoABorrar.value = null
}

// ─── Historial drawer ───────────────────────────────────────────────────────
const drawerVisible     = ref(false)
const contactoHistorial = ref<Contacto | null>(null)
const abrirHistorial = (c: Contacto) => { contactoHistorial.value = c; drawerVisible.value = true; cargarHistorial(c.id) }

// ─── Seguimiento rápido ─────────────────────────────────────────────────────
const modalSegVisible   = ref(false)
const contactoSegActual = ref<Contacto | null>(null)
const abrirSeguimiento = (c: Contacto) => { contactoSegActual.value = c; modalSegVisible.value = true }

// ─── Exportar a Excel ───────────────────────────────────────────────────────
// Exporta lo que el usuario está viendo en la tabla (respeta búsqueda y filtros activos),
// no siempre el listado completo de contactos.
const exportarContactos = () => exportarContactosExcel(contactosFiltrados.value)
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">

    <!-- ── Page Header ──────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-[18px] font-bold text-[#0F172A] dark:text-slate-100 flex items-center gap-2">
          Gestión de Contactos
          <span class="bg-[#EEF2FF] dark:bg-blue-950/50 text-slate-900 dark:text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full">{{ contactos.length }}</span>
        </h2>
        <p class="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">Administra contactos, cargos, etiquetas y seguimientos</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="exportarContactos" class="flex items-center gap-1.5 h-9 px-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
          <Download :size="13" /> Exportar
        </button>
        <button v-if="puedeGestionar" @click="abrirNuevo" class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all">
          <Plus :size="14" /> Nuevo contacto
        </button>
      </div>
    </div>

    <!-- ── Toolbar ───────────────────────────────────────────────── -->
    <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm px-4 py-3">
      <div class="flex flex-col xl:flex-row gap-3 items-start xl:items-center">
        <div class="relative w-full xl:w-[380px] xl:shrink-0">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
          <input v-model="buscar" placeholder="Buscar por documento, empresa o nombre..." title="Buscar por nombre, correo, empresa o documento"
            class="w-full h-9 pl-9 pr-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] text-slate-900 dark:text-slate-100 outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all truncate" />
        </div>
        <div class="grid grid-cols-3 gap-2 w-full xl:flex xl:flex-wrap xl:items-center xl:flex-1">
          <select v-model="filtroEstado" class="w-full xl:flex-1 xl:min-w-[155px] xl:max-w-[240px] h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todos">Estado: Todos</option>
            <option v-for="e in ESTADO_CONTACTO_OPTIONS" :key="e" :value="e">{{ e }}</option>
          </select>
          <select v-model="filtroTipoContacto" class="w-full xl:flex-1 xl:min-w-[170px] xl:max-w-[240px] h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todos">Tipo de contacto: Todos</option>
            <option v-for="t in TIPO_CONTACTO_OPTIONS" :key="t" :value="t">{{ t }}</option>
          </select>
          <select v-model="filtroCiudad" class="w-full xl:flex-1 xl:min-w-[185px] xl:max-w-[260px] h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todas">Ciudad: Todas</option>
            <option v-for="ciudad in ciudades" :key="ciudad" :value="ciudad">{{ ciudad }}</option>
          </select>
          <select v-model="filtroDepartamento" class="w-full xl:flex-1 xl:min-w-[210px] xl:max-w-[280px] h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todos">Departamento: Todos</option>
            <option v-for="depto in departamentosLista" :key="depto" :value="depto">{{ depto }}</option>
          </select>
          <select v-model="filtroResponsable" class="w-full xl:flex-1 xl:min-w-[195px] xl:max-w-[270px] h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todos">Responsable: Todos</option>
            <option v-for="r in responsables" :key="r" :value="r">{{ r }}</option>
          </select>
          <select v-model="filtroSexo" class="w-full xl:flex-1 xl:min-w-[140px] xl:max-w-[220px] h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todos">Sexo: Todos</option>
            <option value="Masculino">Masculino</option>
            <option value="Femenino">Femenino</option>
          </select>
          <select v-model="filtroEdad" class="w-full xl:flex-1 xl:min-w-[145px] xl:max-w-[220px] h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[11px] font-medium text-slate-600 dark:text-slate-300 outline-none cursor-pointer">
            <option value="todos">Edad: Todos</option>
            <option value="0-17">0 – 17 años</option>
            <option value="18-35">18 – 35 años</option>
            <option value="36-50">36 – 50 años</option>
            <option value="51+">51+ años</option>
          </select>
          <button v-if="filtrosActivos > 0" @click="limpiarFiltros"
            class="w-full xl:flex-1 xl:min-w-[130px] xl:max-w-[220px] flex items-center justify-center gap-1 h-9 px-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/40 text-[11px] font-semibold text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 transition-all">
            <X :size="12" /> Limpiar ({{ filtrosActivos }})
          </button>
        </div>
      </div>
      <div class="mt-2 text-[11px] text-slate-400 dark:text-slate-500">
        <template v-if="cargandoContactos">Cargando contactos...</template>
        <template v-else>
          Mostrando <strong class="text-slate-600 dark:text-slate-300">{{ contactosFiltrados.length }}</strong> contactos
          <span v-if="buscar || filtrosActivos > 0"> · filtrado de {{ contactos.length }} total</span>
        </template>
      </div>
      <p v-if="errorContactos" class="mt-1 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorContactos }}</p>
      <p v-if="errorEliminarContacto" class="mt-1 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorEliminarContacto }}</p>
      <p v-if="errorCambiarEstado" class="mt-1 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorCambiarEstado }}</p>
    </div>

    <!-- ── Table ─────────────────────────────────────────────────── -->
    <ContactosTable
      :rows="paginado"
      :pagina-actual="paginaActual"
      :total-paginas="totalPaginas"
      :cambiando-estado-id="cambiandoEstadoId"
      :puede-gestionar="puedeGestionar"
      :puede-eliminar="puedeEliminar"
      @editar="abrirEditar"
      @historial="abrirHistorial"
      @seguimiento="abrirSeguimiento"
      @toggle-estado="alternarEstadoContacto"
      @borrar="pedirBorrarContacto"
      @update:pagina-actual="paginaActual = $event"
    />

    <ContactoFormDialog
      v-model:visible="modalVisible"
      v-model:draft="draft"
      :modo="modalModo"
      :guardando="guardandoContacto"
      :error="errorGuardarContacto"
      :etiquetas="etiquetas"
      :cargando-etiquetas="cargandoEtiquetas"
      :creando-etiqueta="creandoEtiqueta"
      :error-crear-etiqueta="errorCrearEtiqueta"
      :crear-etiqueta="crearEtiqueta"
      :empresas="empresas"
      :cargando-empresas="cargandoEmpresas"
      @submit="guardarContacto"
    />

    <SeguimientoDialog
      v-model:visible="modalSegVisible"
      :contacto="contactoSegActual"
    />

    <HistorialDrawer
      v-model:visible="drawerVisible"
      :contacto="contactoHistorial"
      :items="historialActual"
      :cargando="cargandoHistorial"
      @registrar="contactoHistorial && abrirSeguimiento(contactoHistorial)"
    />

    <ConfirmDialog
      v-model:visible="confirmBorrarVisible"
      titulo="Eliminar contacto"
      :mensaje="`¿Eliminar a ${contactoABorrar?.nombre}? Esta acción no se puede deshacer.`"
      @confirmar="confirmarBorrado"
    />
  </div>
</template>
