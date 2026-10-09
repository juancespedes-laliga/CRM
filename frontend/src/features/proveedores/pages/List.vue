<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Plus, Download } from 'lucide-vue-next'
import type { Proveedor, ProveedorDraft } from '../types/proveedor'
import { PROVEEDOR_DRAFT_VACIO } from '../constants/proveedores.constants'
import { useProveedores } from '../composables/useProveedores'
import { exportarProveedoresExcel } from '../utils/exportarProveedoresExcel'
import ProveedorFormDialog from '../dialogs/ProveedorFormDialog.vue'
import ProveedoresTable from '../tables/ProveedoresTable.vue'
import ProveedorServiciosDrawer from '../dialogs/ProveedorServiciosDrawer.vue'
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'

const { gestionar: puedeGestionar, eliminar: puedeEliminar } = permisosDeModulo('proveedores')

const {
  proveedores, cargandoProveedores, errorProveedores, cargarProveedores,
  buscar, filtroEstado, filtroCategoria,
  proveedoresFiltrados, categorias,
  crearProveedor, actualizarProveedor, errorGuardarProveedor,
  eliminarProveedor, errorEliminarProveedor,
} = useProveedores()

onMounted(() => { cargarProveedores() })

const modalVisible = ref(false)
const modalModo = ref<'nuevo' | 'editar'>('nuevo')
const proveedorEditando = ref<Proveedor | null>(null)
const draft = ref<ProveedorDraft>({ ...PROVEEDOR_DRAFT_VACIO })

const abrirNuevo = () => {
  modalModo.value = 'nuevo'
  proveedorEditando.value = null
  draft.value = { ...PROVEEDOR_DRAFT_VACIO }
  modalVisible.value = true
}
const abrirEditar = (p: Proveedor) => {
  modalModo.value = 'editar'
  proveedorEditando.value = p
  draft.value = { ...p }
  modalVisible.value = true
}
const guardar = async () => {
  const ok = modalModo.value === 'nuevo'
    ? await crearProveedor(draft.value)
    : proveedorEditando.value ? await actualizarProveedor(proveedorEditando.value.id, draft.value) : false
  if (ok) modalVisible.value = false
}
const confirmBorrarVisible = ref(false)
const proveedorABorrar = ref<Proveedor | null>(null)
const pedirBorrarProveedor = (p: Proveedor) => {
  proveedorABorrar.value = p
  errorEliminarProveedor.value = null
  confirmBorrarVisible.value = true
}
const confirmarBorrado = async () => {
  if (proveedorABorrar.value) await eliminarProveedor(proveedorABorrar.value.id)
  proveedorABorrar.value = null
}

const serviciosDrawerVisible = ref(false)
const proveedorServicios = ref<Proveedor | null>(null)
const abrirServicios = (p: Proveedor) => {
  proveedorServicios.value = p
  serviciosDrawerVisible.value = true
}

const exportar = () => exportarProveedoresExcel(
  proveedoresFiltrados.value,
  buscar.value,
  filtroEstado.value,
  filtroCategoria.value,
)
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
          Gestión de Proveedores
          <span class="bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 dark:text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full">{{ proveedores.length }}</span>
        </h2>
        <p class="text-[12px] text-muted mt-0.5">Proveedores registrados por categoría y estado</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="exportar" class="flex items-center gap-1.5 h-9 px-4 rounded-lg border-default surface-card text-[11px] font-semibold text-body surface-hover transition-all">
          <Download :size="13" /> Exportar
        </button>
        <button v-if="puedeGestionar" @click="abrirNuevo" class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all">
          <Plus :size="14" /> Nuevo proveedor
        </button>
      </div>
    </div>

    <div class="surface-card rounded-2xl shadow-sm px-4 py-3">
      <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
        <div class="relative flex-1 min-w-0">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
          <input v-model="buscar" placeholder="Buscar por nombre, NIT, correo o categoría..." class="w-full h-9 pl-9 pr-4 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
        <div class="flex items-center gap-2">
          <select v-model="filtroEstado" class="h-9 px-3 rounded-lg input-surface text-[11px] font-medium text-body outline-none cursor-pointer">
            <option value="todos">Estado: Todos</option>
            <option value="Activo">Activo</option>
            <option value="Inactivo">Inactivo</option>
          </select>
          <select v-model="filtroCategoria" class="h-9 px-3 rounded-lg input-surface text-[11px] font-medium text-body outline-none cursor-pointer">
            <option value="todas">Categoría: Todas</option>
            <option v-for="cat in categorias" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>
      </div>
      <div class="mt-2 text-[11px] text-muted">
        <template v-if="cargandoProveedores">Cargando proveedores...</template>
        <template v-else>Mostrando <strong class="text-body">{{ proveedoresFiltrados.length }}</strong> proveedores</template>
      </div>
      <p v-if="errorProveedores" class="mt-1 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorProveedores }}</p>
      <p v-if="errorEliminarProveedor" class="mt-1 text-[11px] font-medium text-red-500 dark:text-red-400">{{ errorEliminarProveedor }}</p>
    </div>

    <ProveedoresTable
      :rows="proveedoresFiltrados"
      :puede-gestionar="puedeGestionar"
      :puede-eliminar="puedeEliminar"
      @editar="abrirEditar"
      @borrar="pedirBorrarProveedor"
      @servicios="abrirServicios"
    />

    <ProveedorFormDialog
      v-model:visible="modalVisible"
      v-model:draft="draft"
      :modo="modalModo"
      :error="errorGuardarProveedor"
      @submit="guardar"
    />

    <ConfirmDialog
      v-model:visible="confirmBorrarVisible"
      titulo="Eliminar proveedor"
      :mensaje="`¿Eliminar a ${proveedorABorrar?.nombre}? Esta acción no se puede deshacer.`"
      @confirmar="confirmarBorrado"
    />

    <ProveedorServiciosDrawer
      v-model:visible="serviciosDrawerVisible"
      :proveedor="proveedorServicios"
    />
  </div>
</template>
