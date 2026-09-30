<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth, tienePermiso } from '@/features/auth/composables/useAuth'
import { useTema } from '@/shared/composables/useTema'

import {
  LayoutDashboard, Heart, Users, Building2, Truck,
  BookOpen, Target, Filter, Wrench, Upload, Zap, Send,
  ChevronLeft, ChevronRight, LogOut, Settings,
  RefreshCw, X, Menu, Moon, Sun, CalendarClock, CalendarRange
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const { me, logout, checkSession, fetchMe } = useAuth()
const { esOscuro, alternarTema } = useTema()

const initials = computed(() => {
  const parts = (me.value?.nombres ?? '').trim().split(/\s+/).filter(Boolean)
  const letters = parts.slice(0, 2).map((p) => p[0]).join('').toUpperCase()
  return letters || 'PL'
})

// Vigila el token mientras el usuario está inactivo en una ruta (sin navegar)
// para que, al expirar, se lo devuelva al login sin esperar a la próxima navegación.
let sessionWatcher: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  fetchMe()
  sessionWatcher = setInterval(() => {
    if (!checkSession()) {
      router.push('/login')
    }
  }, 30_000)
})
onUnmounted(() => {
  if (sessionWatcher) clearInterval(sessionWatcher)
})

type Vista =
  | 'dashboard' | 'plan-liga' | 'plan-liga-vencimientos' | 'plan-liga-renovaciones' | 'contactos' | 'empresas' | 'proveedores'
  | 'servicios' | 'oportunidades' | 'embudos'
  | 'relacionamiento' | 'campanas' | 'importacion' | 'automatizaciones'

interface Tab { key: Vista; label: string; icono: any; modulo: string }

// ── Menu ──────────────────────────────────────────────────────────
interface MenuGroup { label?: string; items: Tab[] }

// `modulo` es la clave de permisos de cada ítem (coincide con MODULO en
// INTRANET_PERMISOS_APP: "contactos", "bitacora", etc. - ver
// readme/CONSULTAS_EJEMPLO_PERMISOS_APP.md). Un ítem solo se muestra si el
// usuario tiene "<modulo>:ver" en sus permisos (filtrado más abajo en
// menuGroupsVisibles), así que el menú entero queda armado según su rol sin
// tocar esta lista a mano por ambiente/negocio.
const menuGroups: MenuGroup[] = [
  { items: [
    { key: 'dashboard',        label: 'Dashboard',                 icono: LayoutDashboard, modulo: 'dashboard'       },
  ]},
  { label: 'Plan Liga', items: [
    { key: 'plan-liga',              label: 'Titulares y Beneficiarios',   icono: Heart,         modulo: 'planliga' },
    { key: 'plan-liga-vencimientos', label: 'Recordatorios de vencimiento', icono: CalendarClock, modulo: 'recordatorios' },
    { key: 'plan-liga-renovaciones', label: 'Renovaciones por mes',        icono: CalendarRange, modulo: 'planliga' },
  ]},
  { label: 'Comercial', items: [
    { key: 'contactos',        label: 'Contactos',                 icono: Users,           modulo: 'contactos'       },
    { key: 'empresas',         label: 'Empresas',                  icono: Building2,       modulo: 'empresas'        },
    { key: 'proveedores',      label: 'Proveedores',               icono: Truck,           modulo: 'proveedores'     },
    { key: 'oportunidades',    label: 'Oportunidades',             icono: Target,          modulo: 'oportunidades'   },
    { key: 'embudos',          label: 'Embudos',                   icono: Filter,          modulo: 'embudos'         },
    { key: 'servicios',        label: 'Servicios',                 icono: Wrench,          modulo: 'servicios'       },
  ]},
  { label: 'Marketing', items: [
    { key: 'campanas',         label: 'Campañas',                  icono: Send,            modulo: 'campanas'        },
    { key: 'automatizaciones', label: 'Automatizaciones',           icono: Zap,             modulo: 'automatizaciones'},
  ]},
  { label: 'Operaciones', items: [
    { key: 'relacionamiento',  label: 'Bitácora',                  icono: BookOpen,        modulo: 'bitacora'        },
    { key: 'importacion',      label: 'Importación',               icono: Upload,          modulo: 'importacion'     },
  ]},
]

// Solo grupos/ítems donde el usuario tiene "<modulo>:ver". Un grupo que
// queda sin ítems visibles no se muestra (ni su encabezado).
const menuGroupsVisibles = computed<MenuGroup[]>(() =>
  menuGroups
    .map((g) => ({ ...g, items: g.items.filter((i) => tienePermiso(`${i.modulo}:ver`)) }))
    .filter((g) => g.items.length > 0),
)

// ── Tabs ──────────────────────────────────────────────────────────
const MAX_TABS = 4
const tabs = ref<Tab[]>([])

// El hub "Embudos" tiene varias sub-vistas (/embudos/*, /segmentos): todas
// mantienen "Embudos" activo en el menú y comparten una sola pestaña.
const rutaAVista = (path: string): Vista => {
  const p = path.replace(/^\//, '') || 'dashboard'
  if (p === 'embudos' || p.startsWith('embudos/') || p === 'segmentos') return 'embudos'
  return p as Vista
}

// La pestaña activa se deriva siempre de la ruta (no de un índice guardado aparte),
// así que reordenar las pestañas por drag & drop nunca desincroniza cuál está activa.
const vistaActiva  = computed<Vista>(() => rutaAVista(route.path))
const activeTabIdx = computed(() => tabs.value.findIndex(t => t.key === vistaActiva.value))

const findMenuItem = (key: string): Tab | undefined => {
  for (const g of menuGroups) {
    const item = g.items.find(i => i.key === key)
    if (item) return item
  }
  return undefined
}

// Sincroniza las pestañas con la ruta activa (deep-linking / navegación directa por URL).
watch(() => route.path, (path, pathAnterior) => {
  const key = rutaAVista(path)
  if (tabs.value.some(t => t.key === key)) return

  const item = findMenuItem(key)
  if (!item) return

  if (tabs.value.length < MAX_TABS) {
    tabs.value.push(item)
    return
  }

  // Al tope de pestañas: reemplaza la que estaba activa antes de esta navegación.
  const keyAnterior = pathAnterior ? rutaAVista(pathAnterior) : 'dashboard'
  const idxAnterior = tabs.value.findIndex(t => t.key === keyAnterior)
  tabs.value.splice(idxAnterior !== -1 ? idxAnterior : 0, 1, item)
}, { immediate: true })

const navigateTo = (item: Tab) => {
  router.push('/' + item.key)
  sidebarMobileOpen.value = false
}

const goToTab = (idx: number) => {
  router.push('/' + tabs.value[idx].key)
}

const closeTab = (idx: number, e: MouseEvent) => {
  e.stopPropagation()
  if (tabs.value.length === 1) return
  const wasActive = idx === activeTabIdx.value
  tabs.value.splice(idx, 1)
  if (wasActive) {
    const nextIdx = Math.min(idx, tabs.value.length - 1)
    router.push('/' + tabs.value[nextIdx].key)
  }
}

// Reordenar pestañas por drag & drop.
const tabArrastrandoIdx = ref<number | null>(null)
const iniciarArrastreTab = (idx: number, e: DragEvent) => {
  tabArrastrandoIdx.value = idx
  e.dataTransfer?.setData('text/plain', String(idx))
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}
const soltarTab = (idx: number) => {
  const origen = tabArrastrandoIdx.value
  tabArrastrandoIdx.value = null
  if (origen === null || origen === idx) return
  const [movida] = tabs.value.splice(origen, 1)
  tabs.value.splice(idx, 0, movida)
}

const handleLogout = () => {
  logout()
  router.push('/login')
}

// ── Menú de usuario (avatar del header) ──────────────────────────
const menuUsuarioAbierto = ref(false)
const toggleMenuUsuario = () => { menuUsuarioAbierto.value = !menuUsuarioAbierto.value }
const cerrarMenuUsuarioAfuera = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.menu-usuario-trigger') && !target.closest('.menu-usuario-panel')) {
    menuUsuarioAbierto.value = false
  }
}
onMounted(() => document.addEventListener('click', cerrarMenuUsuarioAfuera))
onUnmounted(() => document.removeEventListener('click', cerrarMenuUsuarioAfuera))

// ── Misc ──────────────────────────────────────────────────────────
const sidebarCollapsed = ref(false)
// En móvil el sidebar es un drawer superpuesto (no ocupa espacio del layout);
// se abre con el botón hamburguesa y se cierra al navegar o tocar el fondo.
const sidebarMobileOpen = ref(false)

const activeLabel = computed(() => {
  for (const g of menuGroups) {
    const f = g.items.find(i => i.key === vistaActiva.value)
    if (f) return f.label
  }
  return ''
})
const activeGroup = computed(() => {
  for (const g of menuGroups) {
    if (g.items.find(i => i.key === vistaActiva.value)) return g.label ?? 'General'
  }
  return ''
})

// La página de Configuración se abre desde el avatar, no desde el menú lateral:
// no forma parte del sistema de tabs, así que se maneja como vista independiente.
const isConfigRoute = computed(() => route.path === '/configuracion')

// Botón de refrescar del header: fuerza el remount SOLO de la ruta activa (contador por ruta,
// no global) para que vuelva a ejecutar su carga de datos sin importar la vista en la que se esté.
// Las demás pestañas, cacheadas por el <keep-alive>, no se ven afectadas.
const refreshPorRuta = ref<Record<string, number>>({})
const refrescarVistaActual = () => {
  refreshPorRuta.value[route.path] = (refreshPorRuta.value[route.path] ?? 0) + 1
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-[#F8FAFC] dark:bg-slate-900 font-[Inter,system-ui,sans-serif]">

    <!-- Fondo oscuro tras el sidebar cuando está abierto como drawer en móvil -->
    <div
      v-if="sidebarMobileOpen"
      @click="sidebarMobileOpen = false"
      class="fixed inset-0 bg-black/40 z-20 md:hidden"
    />

    <!-- ═══════════════════════════════════════════════
         SIDEBAR  —  lighter royal blue
    ═══════════════════════════════════════════════ -->
    <aside
      class="flex flex-col shrink-0 overflow-hidden transition-all duration-300 z-30 fixed md:relative inset-y-0 left-0 md:translate-x-0"
      :class="sidebarMobileOpen ? 'translate-x-0' : '-translate-x-full'"
      style="background-color: #295FD3"
      :style="{ width: sidebarCollapsed ? '64px' : '224px' }"
    >
      <!-- Logo -->
      <div class="shrink-0 overflow-hidden">
        <!-- Expandido -->
        <div v-if="!sidebarCollapsed" class="flex flex-col items-center justify-center py-5 px-4 gap-3">
          <div class="text-center">
            <div class="text-[10px] font-bold uppercase tracking-widest text-white/50 leading-none">Plataforma</div>
            <div class="text-[16px] font-black text-white tracking-wide mt-1">CRM Mercadeo</div>
          </div>
          <img
            src="/logo-liga-50.png"
            alt="La Liga"
            class="w-full object-contain select-none pointer-events-none"
            style="max-height: 130px"
          />
        </div>
        <!-- Colapsado -->
        <div v-else class="flex items-center justify-center h-16 bg-white/10">
          <img
            src="/logo-liga-50.png"
            alt="La Liga"
            class="h-8 w-auto object-contain select-none pointer-events-none brightness-0 invert"
          />
        </div>
        <div class="h-px bg-white/10" />
      </div>

      <!-- Nav -->
      <nav class="flex-1 overflow-y-auto py-3 scrollbar-sidebar">
        <template v-for="group in menuGroupsVisibles" :key="group.label ?? '__root__'">
          <!-- Divider for collapsed state -->
          <div v-if="group.label && sidebarCollapsed" class="px-3 py-2">
            <div class="h-px bg-white/15 rounded" />
          </div>
          <!-- Section label -->
          <div
            v-if="group.label && !sidebarCollapsed"
            class="px-4 pt-4 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-white opacity-100 select-none"
          >
            {{ group.label }}
          </div>
          <!-- Items -->
          <button
            v-for="item in group.items"
            :key="item.key"
            @click="navigateTo(item)"
            :title="sidebarCollapsed ? item.label : undefined"
            class="flex items-center gap-3 rounded-lg mx-2 px-2 py-2 transition-all text-left w-[calc(100%-16px)] group/item"
            :class="!isConfigRoute && vistaActiva === item.key
          ? 'bg-white/20 text-white'
          : 'text-white hover:text-white hover:bg-white/10'"
          >
            <component
              :is="item.icono"
              :size="16"
              class="shrink-0 transition-colors"
              :class="!isConfigRoute && vistaActiva === item.key ? 'text-white' : 'text-white/80'"
            />
            <span
              v-if="!sidebarCollapsed"
              class="text-[12px] font-semibold truncate flex-1 !text-white"
            >
              {{ item.label }}
            </span>
            <!-- Active dot -->
            <span
              v-if="!isConfigRoute && vistaActiva === item.key && !sidebarCollapsed"
              class="w-1.5 h-1.5 rounded-full bg-white shrink-0"
            />
            <!-- Tab indicator: small badge showing it's open in a tab -->
            <span
              v-else-if="tabs.some(t => t.key === item.key) && !sidebarCollapsed && (isConfigRoute || vistaActiva !== item.key)"
              class="w-1.5 h-1.5 rounded-full bg-white/40 shrink-0"
            />
          </button>
        </template>
      </nav>

      <!-- Logout -->
      <div class="shrink-0 border-t border-white/10 p-2">
        <button
          @click="handleLogout"
          :title="sidebarCollapsed ? 'Cerrar sesión' : undefined"
          class="flex items-center gap-3 w-full rounded-lg px-2 py-2 hover:bg-white/10 transition-all group/logout"
        >
          <LogOut :size="15" class="shrink-0 text-white/80 group-hover/logout:text-white transition-colors" />
          <span v-if="!sidebarCollapsed" class="text-[12px] font-semibold !text-white">Cerrar sesión</span>
        </button>
      </div>
    </aside>

    <!-- ═══════════════════════════════════════════════
         MAIN AREA
    ═══════════════════════════════════════════════ -->
    <div class="flex-1 flex flex-col overflow-hidden min-w-0">

      <!-- ── Top header ────────────────────────────────────────── -->
      <header class="h-14 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-3 md:px-4 shrink-0 gap-2 md:gap-3 z-10">
        <div class="flex items-center gap-2 md:gap-3 min-w-0">
          <!-- Hamburguesa: solo móvil, abre el sidebar como drawer -->
          <button
            @click="sidebarMobileOpen = true"
            class="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shrink-0 md:hidden"
          >
            <Menu :size="15" />
          </button>
          <!-- Toggle sidebar: solo desktop/tablet, colapsa a modo íconos -->
          <button
            @click="sidebarCollapsed = !sidebarCollapsed"
            class="hidden md:flex w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700 items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all shrink-0"
          >
            <component :is="sidebarCollapsed ? ChevronRight : ChevronLeft" :size="15" />
          </button>
          <!-- Breadcrumb -->
          <div class="flex items-center gap-1.5 text-[12px] min-w-0 overflow-hidden">
            <span class="text-slate-400 dark:text-slate-500 shrink-0">CRM Mercadeo</span>
            <template v-if="isConfigRoute">
              <span class="text-slate-300 dark:text-slate-600 shrink-0">/</span>
              <span class="font-bold text-[#0F172A] dark:text-slate-100 truncate">Configuración</span>
            </template>
            <template v-else>
              <template v-if="activeGroup && activeGroup !== 'General'">
                <span class="text-slate-300 dark:text-slate-600 shrink-0 hidden sm:inline">/</span>
                <span class="text-slate-400 dark:text-slate-500 shrink-0 hidden sm:inline">{{ activeGroup }}</span>
              </template>
              <span class="text-slate-300 dark:text-slate-600 shrink-0">/</span>
              <span class="font-bold text-[#0F172A] dark:text-slate-100 truncate">{{ activeLabel }}</span>
            </template>
          </div>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <button
            @click="refrescarVistaActual"
            class="h-9 px-3.5 rounded-lg bg-[#EC4899] hover:bg-[#D61F69] flex items-center gap-1.5 text-white shadow transition-all"
            title="Actualizar"
          >
            <span class="text-[12px] font-bold hidden sm:inline">Actualizar</span>
            <RefreshCw :size="14" />
          </button>

          <!-- Toggle de tema: un clic directo -->
          <button
            type="button"
            @click="alternarTema"
            :title="esOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
            :aria-label="esOscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
            class="w-9 h-9 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-[#1E3A8A] dark:hover:text-blue-300 transition-all shrink-0"
          >
            <component :is="esOscuro ? Sun : Moon" :size="16" class="shrink-0" />
          </button>

          <div class="relative">
            <button
              type="button"
              @click="toggleMenuUsuario"
              class="menu-usuario-trigger flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-all py-1 pr-1"
            >
              <div class="text-right hidden sm:block leading-tight">
                <div class="text-[13px] font-bold text-[#0F172A] dark:text-slate-100 whitespace-nowrap">{{ me?.nombres ?? '—' }}</div>
                <div class="text-[11px] text-slate-400 dark:text-slate-500 font-bold uppercase tracking-wider">{{ me?.portal_role ?? '' }}</div>
              </div>
              <div
                class="h-8 w-8 rounded-lg bg-[#1E3A8A] text-white text-[10px] font-bold flex items-center justify-center select-none shrink-0"
                :title="me?.nombres"
              >
                {{ initials }}
              </div>
            </button>

            <div
              v-if="menuUsuarioAbierto"
              class="menu-usuario-panel absolute right-0 top-full mt-2 w-48 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg py-1.5 z-30"
            >
              <button
                @click="menuUsuarioAbierto = false; router.push('/configuracion')"
                class="flex items-center gap-2 w-full px-3 py-2 text-[12px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
              >
                <Settings :size="14" class="shrink-0" />
                Configuración
              </button>
              <button
                @click="menuUsuarioAbierto = false; handleLogout()"
                class="flex items-center gap-2 w-full px-3 py-2 text-[12px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
              >
                <LogOut :size="14" class="shrink-0" />
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- ── Tab strip ─────────────────────────────────────────── -->
      <div v-if="!isConfigRoute" class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 px-3 flex items-end gap-0.5 shrink-0 overflow-x-auto">
        <button
          v-for="(tab, idx) in tabs"
          :key="tab.key"
          draggable="true"
          @click="goToTab(idx)"
          @dragstart="iniciarArrastreTab(idx, $event)"
          @dragover.prevent
          @drop.prevent="soltarTab(idx)"
          @dragend="tabArrastrandoIdx = null"
          class="flex items-center gap-1.5 px-3 py-2.5 text-[11px] font-semibold border-b-2 transition-all shrink-0 group/tab rounded-t-lg hover:bg-slate-50 dark:hover:bg-slate-800 cursor-grab active:cursor-grabbing"
          :class="[
            idx === activeTabIdx
              ? 'border-[#1E3A8A] text-[#1E3A8A] dark:text-blue-300 bg-[#EEF2FF]/60 dark:bg-blue-950/40'
              : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200',
            tabArrastrandoIdx === idx ? 'opacity-40' : '',
          ]"
        >
          <component :is="tab.icono" :size="12" class="shrink-0" />
          <span class="max-w-[120px] truncate">{{ tab.label }}</span>
          <span
            v-if="tabs.length > 1"
            class="w-4 h-4 rounded flex items-center justify-center ml-0.5 opacity-0 group-hover/tab:opacity-100 hover:!bg-slate-200 dark:hover:!bg-slate-700 transition-all"
            :class="idx === activeTabIdx ? 'text-[#1E3A8A] dark:text-blue-300 hover:bg-[#DBEAFE]' : 'text-slate-400 dark:text-slate-500 hover:bg-slate-100'"
            @click.stop="closeTab(idx, $event)"
          >
            <X :size="9" />
          </span>
        </button>
        <!-- Slot count indicator when at max -->
        <div
          v-if="tabs.length >= MAX_TABS"
          class="ml-auto px-2 py-2 text-[10px] text-slate-400 dark:text-slate-500 font-semibold shrink-0 self-center"
        >
          {{ MAX_TABS }}/{{ MAX_TABS }} pestañas
        </div>
      </div>

      <!-- ── Content ───────────────────────────────────────────── -->
      <main
        class="flex-1 min-h-0 overflow-y-auto p-3 sm:p-4 md:p-6"
      >
        <router-view v-slot="{ Component, route: rutaActiva }">
          <keep-alive :max="8">
            <component :is="Component" :key="`${rutaActiva.path}::${refreshPorRuta[rutaActiva.path] ?? 0}`" />
          </keep-alive>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Antes el menú usaba scrollbar-none (invisible): cuando había más módulos de los que caben
   en pantalla, no había ninguna señal de que se podía hacer scroll. Esta barra delgada, clara
   sobre el fondo azul del menú, queda siempre visible como indicación (no solo al pasar el mouse). */
.scrollbar-sidebar::-webkit-scrollbar {
  width: 5px;
}

.scrollbar-sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.25);
  border-radius: 3px;
}

.scrollbar-sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.45);
}

.scrollbar-sidebar {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
}
</style>
