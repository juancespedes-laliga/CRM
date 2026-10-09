<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Upload, Pencil, Trash2, UsersRound, Loader2, AlertCircle, X, ChevronRight, Lock, Filter, RefreshCw, UserPlus, Download, Info } from 'lucide-vue-next'
import type { CategoriaGrupo, GrupoDraft, MiembroGrupo } from '../types/grupo'
import { GRUPO_DRAFT_VACIO } from '../constants/grupos.constants'
import { useGruposInteres } from '../composables/useGruposInteres'
import CategoriasPanel from '../components/CategoriasPanel.vue'
import MiembrosTable from '../tables/MiembrosTable.vue'
import GrupoFormDialog from '../dialogs/GrupoFormDialog.vue'
import CargarBaseDialog from '../dialogs/CargarBaseDialog.vue'
import AgregarPersonaDialog from '../dialogs/AgregarPersonaDialog.vue'
import { descargarPlantillaGrupo } from '../utils/cargaGrupo'
import { normalizarNombre } from '../utils/normalizar'
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue'
import AudienciasSubnav from '@/features/embudos/components/AudienciasSubnav.vue'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'

const router = useRouter()

// TODO: cuando exista el backend, crear el módulo de permisos "grupos" (ver/gestionar/eliminar)
// en INTRANET_PERMISOS_APP y cambiar esto a 'grupos'. Hoy usa el de contactos.
const { gestionar: puedeGestionar, eliminar: puedeEliminar } = permisosDeModulo('contactos')

const {
  grupos, cargandoGrupos, grupoId, grupo, categorias, miembros, cargandoDetalle, error,
  buscar, filtroCategoria, filtroCiudad, filtroContacto, ciudades, filtrosMiembrosActivos, limpiarFiltrosMiembros,
  miembrosFiltrados, sinCategoria,
  cargarGrupos, seleccionar, refrescar,
  crearGrupo, actualizarGrupo, eliminarGrupo,
  crearCategoria, renombrarCategoria, eliminarCategoria,
  cambiarCategoriaMiembro, quitarMiembro,
} = useGruposInteres()

onMounted(cargarGrupos)

// Grupo: crear / editar
const formVisible = ref(false)
const formModo = ref<'nuevo' | 'editar'>('nuevo')
const draft = ref<GrupoDraft>({ ...GRUPO_DRAFT_VACIO })
const errorForm = ref<string | null>(null)
const guardando = ref(false)
const abrirNuevo = () => { formModo.value = 'nuevo'; draft.value = { ...GRUPO_DRAFT_VACIO }; errorForm.value = null; formVisible.value = true }
const abrirEditar = () => {
  if (!grupo.value) return
  formModo.value = 'editar'
  draft.value = { nombre: grupo.value.nombre, descripcion: grupo.value.descripcion, color: grupo.value.color }
  errorForm.value = null
  formVisible.value = true
}
const guardarGrupo = async () => {
  guardando.value = true
  const ok = formModo.value === 'nuevo' ? await crearGrupo(draft.value) : grupo.value ? await actualizarGrupo(grupo.value.id, draft.value) : false
  guardando.value = false
  if (ok) formVisible.value = false
  else { errorForm.value = error.value; error.value = null }
}

// Confirmaciones
const confirmVisible = ref(false)
const confirmTitulo = ref('')
const confirmMensaje = ref('')
let accionConfirmada: () => void = () => {}
const pedirConfirmacion = (titulo: string, mensaje: string, accion: () => void) => {
  confirmTitulo.value = titulo; confirmMensaje.value = mensaje; accionConfirmada = accion; confirmVisible.value = true
}
const pedirEliminarGrupo = () => grupo.value && pedirConfirmacion('Eliminar grupo',
  `¿Eliminar el grupo «${grupo.value.nombre}» con sus ${categorias.value.length} categorías? Las personas siguen en Contactos; solo dejan de pertenecer al grupo.`,
  () => grupo.value && eliminarGrupo(grupo.value.id))
const pedirEliminarCategoria = (c: CategoriaGrupo) => pedirConfirmacion('Eliminar categoría',
  `¿Eliminar la categoría «${c.nombre}»? Sus ${c.totalMiembros} miembro(s) quedarán «Sin categoría» dentro del grupo.`,
  () => eliminarCategoria(c.id))
const pedirQuitarMiembro = (m: MiembroGrupo) => pedirConfirmacion('Quitar del grupo',
  `¿Quitar a ${m.nombre} del grupo «${grupo.value?.nombre}»? El contacto no se borra del CRM.`,
  () => quitarMiembro(m.id))

// Agregar miembros: Excel (la vía principal) o una persona a la vez.
const cargaVisible = ref(false)
const personaVisible = ref(false)

// Buscador de la lista de grupos (aparece cuando hay más de 5).
const buscarGrupo = ref('')
const gruposVisibles = computed(() => {
  const q = normalizarNombre(buscarGrupo.value)
  return q ? grupos.value.filter((g) => normalizarNombre(g.nombre).includes(q)) : grupos.value
})
const fecha = (iso: string) => iso.split('-').reverse().join('/')
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <!-- Encabezado común de Audiencias -->
    <div>
      <nav class="flex items-center gap-1.5 text-[12px] mb-1.5">
        <span class="text-slate-400 dark:text-slate-500">CRM Mercadeo</span>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <button class="text-slate-400 dark:text-slate-500 hover:text-[#2447F9] font-semibold transition-colors" @click="router.push('/embudos')">Embudos</button>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <button class="text-slate-400 dark:text-slate-500 hover:text-[#2447F9] font-semibold transition-colors" @click="router.push('/embudos/afiliado')">Audiencias</button>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <span class="font-bold text-[#0F172A] dark:text-slate-100">Grupos de interés</span>
      </nav>
      <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
        <RefreshCw :size="19" class="text-[#EC4899]" /> Audiencias
      </h2>
      <p class="text-[12px] text-body mt-0.5">
        Arma una audiencia con filtros de Plan Liga (o no Plan Liga) y actúa sobre ella, o trabaja con grupos de interés: listas fijas con categorías propias.
      </p>
    </div>

    <AudienciasSubnav />

    <div v-if="error" class="flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-md px-3 py-2">
      <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
      <p class="text-[12px] text-red-600 dark:text-red-400 font-medium flex-1">{{ error }}</p>
      <button @click="error = null" class="text-red-400 hover:text-red-600" title="Cerrar"><X :size="13" /></button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-[264px_minmax(0,1fr)] gap-5 items-start">
      <!-- ── Lista de grupos ─────────────────────────────────── -->
      <aside class="surface-card rounded-lg border border-default shadow-sm overflow-hidden lg:sticky lg:top-0">
        <div class="flex items-center justify-between px-4 h-12 border-b border-default">
          <h3 class="text-[12px] font-bold text-heading">
            Grupos <span class="text-muted font-semibold tabular-nums">({{ grupos.length }})</span>
          </h3>
          <button v-if="puedeGestionar" @click="abrirNuevo" title="Nuevo grupo"
            class="h-7 px-2.5 rounded-md bg-[#2447F9] text-white text-[11px] font-semibold flex items-center gap-1 hover:bg-[#1D3DD9] transition-colors">
            <Plus :size="12" /> Nuevo
          </button>
        </div>
        <div v-if="grupos.length > 5" class="px-3 pt-3">
          <div class="relative">
            <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input v-model="buscarGrupo" placeholder="Buscar grupo…" class="w-full h-8 pl-7 pr-2 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[12px] outline-none focus:border-[#2447F9]" />
          </div>
        </div>
        <div class="p-2">
          <div v-if="cargandoGrupos" class="flex items-center justify-center gap-2 text-[12px] text-muted py-6"><Loader2 :size="14" class="animate-spin" /> Cargando…</div>
          <button v-for="g in gruposVisibles" :key="g.id" @click="seleccionar(g.id)"
            class="relative w-full text-left rounded-md pl-4 pr-3 py-2.5 flex items-center gap-3 transition-colors"
            :class="g.id === grupoId ? 'bg-slate-100 dark:bg-slate-700/60' : 'hover:bg-slate-50 dark:hover:bg-slate-700/30'">
            <span class="absolute left-1.5 top-2.5 bottom-2.5 w-[3px] rounded-sm" :style="{ backgroundColor: g.color }" />
            <span class="min-w-0 flex-1">
              <span class="block text-[12px] truncate" :class="g.id === grupoId ? 'font-bold text-heading' : 'font-semibold text-body'">{{ g.nombre }}</span>
              <span class="block text-[11px] text-muted">{{ g.totalMiembros }} {{ g.totalMiembros === 1 ? 'miembro' : 'miembros' }}</span>
            </span>
          </button>
          <p v-if="!cargandoGrupos && grupos.length === 0" class="text-center text-[12px] text-muted py-6 px-3">Todavía no hay grupos. Cree el primero con «Nuevo».</p>
        </div>
      </aside>

      <!-- ── Detalle del grupo ───────────────────────────────── -->
      <section v-if="grupo" class="space-y-4 min-w-0">
        <div class="surface-card rounded-lg border border-default shadow-sm">
          <div class="px-5 py-4 flex flex-col xl:flex-row xl:items-start gap-4">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="w-2.5 h-2.5 rounded-sm" :style="{ backgroundColor: grupo.color }" />
                <h3 class="text-[16px] font-bold text-heading">{{ grupo.nombre }}</h3>
                <span class="inline-flex items-center gap-1 text-[10px] font-semibold text-body bg-slate-100 dark:bg-slate-700/60 px-1.5 py-0.5 rounded"
                  title="Un grupo de interés es una lista fija: sus miembros solo cambian cuando alguien los agrega, los quita o carga un Excel. A diferencia de la pestaña «Por filtros», no se recalcula.">
                  <Lock :size="10" /> Lista fija
                </span>
              </div>
              <p class="text-[12px] text-body mt-1">{{ grupo.descripcion || 'Sin descripción' }}</p>
              <p class="text-[11px] text-muted mt-1.5 tabular-nums">
                {{ miembros.length }} miembros · {{ categorias.length }} categorías · creado el {{ fecha(grupo.fechaCreacion) }}
              </p>
            </div>
            <div class="flex items-center gap-2 flex-wrap shrink-0">
              <template v-if="puedeGestionar">
                <button @click="personaVisible = true"
                  class="flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[12px] font-semibold text-body hover:border-slate-400 transition-colors">
                  <UserPlus :size="14" /> Agregar persona
                </button>
                <button @click="cargaVisible = true"
                  class="flex items-center gap-1.5 h-9 px-4 rounded-md bg-[#2447F9] text-white text-[12px] font-semibold hover:bg-[#1D3DD9] transition-colors">
                  <Upload :size="14" /> Cargar Excel
                </button>
                <span class="w-px h-6 bg-slate-200 dark:bg-slate-700 mx-1" />
                <button @click="abrirEditar" title="Editar grupo" class="w-9 h-9 rounded-md text-muted hover:text-heading hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center justify-center transition-colors"><Pencil :size="14" /></button>
              </template>
              <button v-if="puedeEliminar" @click="pedirEliminarGrupo" title="Eliminar grupo" class="w-9 h-9 rounded-md text-muted hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center justify-center transition-colors"><Trash2 :size="14" /></button>
            </div>
          </div>
          <div v-if="puedeGestionar" class="px-5 py-2.5 border-t border-default flex items-center gap-1.5 text-[11px] text-muted">
            <Filter :size="12" class="shrink-0" />
            ¿Prefiere elegir personas por plan, edad o ciudad?
            <button @click="router.push('/embudos/afiliado')" class="font-bold text-slate-900 dark:text-white hover:underline">Agregar con filtros</button>
          </div>
        </div>

        <!-- Grupo vacío: la carga por Excel es el camino principal -->
        <div v-if="!cargandoDetalle && miembros.length === 0" class="surface-card rounded-lg border border-dashed border-slate-300 dark:border-slate-600 px-6 py-12 text-center">
          <div class="w-11 h-11 mx-auto rounded-lg bg-[#EEF2FF] dark:bg-blue-950/40 text-slate-900 font-bold dark:text-white flex items-center justify-center">
            <UsersRound :size="20" />
          </div>
          <h4 class="text-[14px] font-bold text-heading mt-4">Este grupo aún no tiene miembros</h4>
          <p class="text-[12px] text-muted mt-1 max-w-md mx-auto">
            Cargue un Excel con todas las personas a la vez. Las categorías que traiga el archivo se crean solas.
          </p>
          <div v-if="puedeGestionar" class="flex items-center justify-center gap-2 mt-5 flex-wrap">
            <button @click="cargaVisible = true" class="flex items-center gap-1.5 h-9 px-4 rounded-md bg-[#2447F9] text-white text-[12px] font-semibold hover:bg-[#1D3DD9] transition-colors">
              <Upload :size="14" /> Cargar Excel
            </button>
            <button @click="personaVisible = true" class="flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[12px] font-semibold text-body hover:border-slate-400 transition-colors">
              <UserPlus :size="14" /> Agregar persona
            </button>
          </div>
          <button @click="descargarPlantillaGrupo(grupo.nombre)" class="mt-3 inline-flex items-center gap-1 text-[11px] font-semibold text-muted hover:text-[#2447F9]">
            <Download :size="12" /> Descargar plantilla de Excel
          </button>
        </div>

        <template v-else>
          <CategoriasPanel
            v-model:filtro="filtroCategoria"
            :categorias="categorias"
            :total-miembros="miembros.length"
            :sin-categoria="sinCategoria"
            :color="grupo.color"
            :puede-gestionar="puedeGestionar"
            @crear="crearCategoria"
            @renombrar="renombrarCategoria"
            @eliminar="pedirEliminarCategoria"
          />

          <div class="surface-card rounded-lg border border-default shadow-sm px-4 py-3">
            <div class="flex flex-col sm:flex-row gap-2">
              <div class="relative flex-1 min-w-0">
                <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
                <input v-model="buscar" placeholder="Buscar por nombre, documento, correo o ciudad…"
                  class="w-full h-9 pl-9 pr-3 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[12px] outline-none focus:border-[#2447F9] transition-colors" />
              </div>
              <select v-model="filtroCiudad" class="h-9 px-3 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[12px] text-body outline-none cursor-pointer">
                <option value="todas">Ciudad: todas</option>
                <option v-for="c in ciudades" :key="c" :value="c">{{ c }}</option>
              </select>
              <select v-model="filtroContacto" class="h-9 px-3 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-900 text-[12px] text-body outline-none cursor-pointer">
                <option value="todos">Contacto: todos</option>
                <option value="con_correo">Con correo</option>
                <option value="con_celular">Con celular</option>
                <option value="sin_correo">Sin correo</option>
              </select>
            </div>
            <div class="mt-2 flex items-center gap-3 text-[11px] text-muted">
              <span v-if="cargandoDetalle">Cargando miembros…</span>
              <span v-else>Mostrando <strong class="text-body tabular-nums">{{ miembrosFiltrados.length }}</strong> de <strong class="text-body tabular-nums">{{ miembros.length }}</strong> miembros</span>
              <button v-if="filtrosMiembrosActivos" @click="limpiarFiltrosMiembros" class="flex items-center gap-1 font-semibold hover:text-[#2447F9]">
                <X :size="11" /> Limpiar filtros ({{ filtrosMiembrosActivos }})
              </button>
            </div>
          </div>

          <MiembrosTable
            :rows="miembrosFiltrados"
            :categorias="categorias"
            :puede-gestionar="puedeGestionar"
            @cambiar-categoria="cambiarCategoriaMiembro"
            @quitar="pedirQuitarMiembro"
          />
        </template>
      </section>
    </div>

    <p class="flex items-center gap-1.5 text-[11px] text-muted">
      <Info :size="12" class="shrink-0" /> Vista previa con datos de ejemplo: los cambios aún no se guardan en la base de datos y se pierden al recargar la página.
    </p>

    <GrupoFormDialog v-model:visible="formVisible" v-model:draft="draft" :modo="formModo" :error="errorForm" :guardando="guardando" @submit="guardarGrupo" />
    <CargarBaseDialog v-model:visible="cargaVisible" :grupo="grupo" :categorias="categorias" @cargado="refrescar" />
    <AgregarPersonaDialog v-model:visible="personaVisible" :grupo="grupo" :categorias="categorias" :miembros="miembros" @agregado="refrescar" />
    <ConfirmDialog v-model:visible="confirmVisible" :titulo="confirmTitulo" :mensaje="confirmMensaje" @confirmar="accionConfirmada()" />
  </div>
</template>
