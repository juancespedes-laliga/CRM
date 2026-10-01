<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  ChevronLeft, ChevronRight, AlertTriangle, CalendarRange,
  Mail, Phone, MessageSquare, ClipboardList, Palette, X,
} from 'lucide-vue-next'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'
import type { Titular } from '../types/plan-liga'
import SeguimientoDialog from '../dialogs/SeguimientoDialog.vue'
import {
  getRenovacionesMes, actualizarColorTitular,
  type ListadoRenovacionesMes, type RenovacionMesItem,
} from '../services/renovaciones.api'

const { ver: puedeVer } = permisosDeModulo('planliga')

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

const hoy = new Date()
const anio = ref(hoy.getFullYear())
const mes = ref(hoy.getMonth() + 1) // 1-12

const cargando = ref(false)
const error = ref<string | null>(null)
const datos = ref<ListadoRenovacionesMes | null>(null)

const cargar = async () => {
  cargando.value = true
  error.value = null
  try {
    datos.value = await getRenovacionesMes(anio.value, mes.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo cargar la información.'
  } finally {
    cargando.value = false
  }
}

const mesAnterior = () => {
  if (mes.value === 1) { mes.value = 12; anio.value -= 1 } else { mes.value -= 1 }
}
const mesSiguiente = () => {
  if (mes.value === 12) { mes.value = 1; anio.value += 1 } else { mes.value += 1 }
}
watch([anio, mes], cargar)

// Las tarjetas del resumen son el filtro de la tabla. "Vencen" es otra lista
// (titulares activos cuyo plan vence ese mes), no un subconjunto del total.
type Vista = 'todos' | 'renovados' | 'altas' | 'vencen'
const vista = ref<Vista>('todos')
const items = computed(() => {
  const d = datos.value
  if (!d) return []
  switch (vista.value) {
    case 'renovados': return d.items.filter(i => i.RENOVADO === 'S')
    case 'altas': return d.items.filter(i => i.RENOVADO !== 'S')
    case 'vencen': return d.vencen ?? []
    default: return d.items
  }
})
const resumen = computed(() => datos.value?.resumen ?? null)

const fmtDia = (iso: string | null) => {
  if (!iso) return '—'
  return new Date(`${iso}T00:00:00`).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}
const fmtFechaHora = (iso: string | null) => {
  if (!iso) return null
  return new Date(iso).toLocaleString('es-CO', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// ─── Paginación (en cliente: la ventana de un mes no llega a miles de filas,
// mismo criterio que Recordatorios de vencimiento) ─────────────────────────
const POR_PAGINA = 10
const pagina = ref(1)
const totalPaginas = computed(() => Math.max(1, Math.ceil(items.value.length / POR_PAGINA)))
const itemsPagina = computed(() => items.value.slice((pagina.value - 1) * POR_PAGINA, pagina.value * POR_PAGINA))
watch(items, () => { pagina.value = 1 })

// ─── Seguimiento (bitácora): mismo diálogo que usa Titulares y Beneficiarios,
// solo hace falta darle un objeto Titular -- los campos que esta consulta no
// trae (dirección, EPS, etc.) no los usa el diálogo, quedan vacíos. ────────
const modalSegVisible = ref(false)
const titularSegActual = ref<Titular | null>(null)
const aTitular = (item: RenovacionMesItem): Titular => ({
  id: item.ID,
  tipoDocumento: item.TIPO_DOCUMENTO ?? '',
  documento: item.DOCUMENTO,
  nombre: item.NOMBRE,
  fechaNacimiento: '',
  sexo: '',
  correo: item.CORREO ?? '',
  telefono: item.TELEFONO ?? '',
  direccion: '',
  ciudad: '',
  departamento: '',
  empresa: item.EMPRESA ?? '',
  planContratado: item.TIPO_PLAN ?? '',
  tipoPlanId: null,
  tipoPlan: item.TIPO_PLAN ?? '',
  tipoAfiliado: '',
  eps: '',
  otraEps: '',
  planSalud: '',
  planNombre: '',
  fechaInscripcion: item.FECHA_INGRESO,
  estado: item.ESTADO === 'A' ? 'Activo' : 'Inactivo',
  factura: '',
})
const abrirSeguimiento = (item: RenovacionMesItem) => {
  titularSegActual.value = aTitular(item)
  modalSegVisible.value = true
}

// ─── Color de fila (compartido: PUT .../{id}/color) ────────────────────────
const PALETA_COLORES = [
  { color: '#FEF08A', nombre: 'Amarillo' },
  { color: '#BBF7D0', nombre: 'Verde' },
  { color: '#FECACA', nombre: 'Rojo' },
  { color: '#BFDBFE', nombre: 'Azul' },
  { color: '#E9D5FF', nombre: 'Morado' },
  { color: '#FED7AA', nombre: 'Naranja' },
]
const menuColorAbierto = ref<number | null>(null)
const menuColorPos = ref({ top: 0, left: 0 })
const guardandoColor = ref<number | null>(null)

// El menu se teleporta a <body> (ver template) para que quede SIEMPRE por
// encima de la tabla y no se pueda ver ni clickear nada de las filas que
// tiene debajo -- dentro de una celda con overflow-x-auto en la tabla, el
// z-index no alcanzaba a ganarle a las filas siguientes.
const toggleMenuColor = (item: RenovacionMesItem, ev: MouseEvent) => {
  if (menuColorAbierto.value === item.ID) { menuColorAbierto.value = null; return }
  const rect = (ev.currentTarget as HTMLElement).getBoundingClientRect()
  menuColorPos.value = { top: rect.bottom + 6, left: rect.left }
  menuColorAbierto.value = item.ID
}
const itemMenuColor = computed(() => items.value.find(i => i.ID === menuColorAbierto.value) ?? null)

const tarjetas = computed(() => {
  const r = resumen.value
  if (!r) return []
  const nombreMes = MESES[mes.value - 1]
  return [
    { vista: 'todos' as const, valor: r.total, titulo: 'Total del mes', texto: `Titulares con fecha de ingreso en ${nombreMes}.`, color: 'text-heading', activo: 'border-slate-400 dark:border-slate-400' },
    { vista: 'renovados' as const, valor: r.renovados, titulo: 'Renovaciones (RENOVADO = S)', texto: 'Ya eran titulares antes y volvieron a activar el plan.', color: 'text-emerald-600 dark:text-emerald-400', activo: 'border-emerald-500' },
    { vista: 'altas' as const, valor: r.altas_nuevas, titulo: 'Altas nuevas (RENOVADO = N)', texto: 'Se registraron en Plan Liga por primera vez.', color: 'text-[#2447F9] dark:text-blue-400', activo: 'border-[#2447F9]' },
    { vista: 'vencen' as const, valor: r.vencen, titulo: `Vencen en ${nombreMes}`, texto: 'Titulares activos cuyo plan cumple un año este mes.', color: 'text-amber-600 dark:text-amber-400', activo: 'border-amber-500' },
  ]
})

const mensajeVacio = computed(() => {
  const periodo = `${MESES[mes.value - 1]} ${anio.value}`
  switch (vista.value) {
    case 'renovados': return `Nadie renovó en ${periodo}.`
    case 'altas': return `No hubo altas nuevas en ${periodo}.`
    case 'vencen': return `Ningún titular activo vence en ${periodo}.`
    default: return `Nadie se activó ni renovó en ${periodo}.`
  }
})

const elegirColor = async (item: RenovacionMesItem, color: string | null) => {
  menuColorAbierto.value = null
  const anterior = item.COLOR
  item.COLOR = color // optimista: se ve al toque, se revierte si falla
  guardandoColor.value = item.ID
  try {
    await actualizarColorTitular(item.ID, color)
  } catch (e) {
    item.COLOR = anterior
    error.value = e instanceof Error ? e.message : 'No se pudo guardar el color.'
  } finally {
    guardandoColor.value = null
  }
}

onMounted(cargar)
</script>

<template>
  <div v-if="!puedeVer" class="surface-card rounded-2xl shadow-sm text-center py-16">
    <AlertTriangle :size="28" class="text-slate-300 dark:text-slate-600 mx-auto mb-3" />
    <p class="text-[13px] font-semibold text-subtle">Sin acceso a este módulo</p>
  </div>

  <div v-else class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div>
      <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
        <CalendarRange :size="20" class="text-[#059669]" />
        Renovaciones por mes · Plan Liga
      </h2>
      <p class="text-[12px] text-body mt-0.5">
        Titulares que se activaron o renovaron en el mes elegido, según su fecha de ingreso.
      </p>
    </div>

    <!-- Selector de mes -->
    <div class="surface-card rounded-2xl shadow-sm px-4 py-3 flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2">
        <button
          @click="mesAnterior"
          class="w-9 h-9 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        ><ChevronLeft :size="16" /></button>
        <span class="text-[14px] font-bold text-heading tabular-nums w-40 text-center">{{ MESES[mes - 1] }} {{ anio }}</span>
        <button
          @click="mesSiguiente"
          class="w-9 h-9 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        ><ChevronRight :size="16" /></button>
      </div>
    </div>

    <!-- Resumen: cada tarjeta filtra la tabla -->
    <div v-if="resumen" class="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <button
        v-for="c in tarjetas" :key="c.vista"
        @click="vista = c.vista"
        class="surface-card rounded-2xl shadow-sm p-4 text-left border-2 transition-all hover:shadow-md"
        :class="vista === c.vista ? c.activo : 'border-transparent'"
      >
        <div class="text-[22px] font-bold leading-none" :class="c.color">{{ c.valor }}</div>
        <div class="text-[10px] font-semibold text-subtle uppercase tracking-wide mt-1">{{ c.titulo }}</div>
        <p class="text-[10px] text-muted mt-1 leading-snug">{{ c.texto }}</p>
      </button>
    </div>

    <div v-if="error" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">
      {{ error }}
    </div>

    <!-- Tabla -->
    <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
      <div class="px-4 py-2.5 border-b border-slate-200 dark:border-slate-700 text-[11px] text-muted">
        Mostrando <strong class="text-body">{{ itemsPagina.length }}</strong> de
        <strong class="text-body">{{ items.length }}</strong> titulares
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-[12px]">
          <thead>
            <tr class="border-b border-slate-200 dark:border-slate-700 text-left text-[11px] uppercase tracking-wide text-subtle">
              <th class="px-4 py-3 font-semibold w-8"></th>
              <th class="px-4 py-3 font-semibold">Titular</th>
              <th class="px-4 py-3 font-semibold">Tipo</th>
              <th class="px-4 py-3 font-semibold">Estado</th>
              <th class="px-4 py-3 font-semibold">Ingreso</th>
              <th class="px-4 py-3 font-semibold">Vence</th>
              <th class="px-4 py-3 font-semibold">Contacto</th>
              <th class="px-4 py-3 font-semibold">Último seguimiento</th>
              <th class="px-4 py-3 font-semibold"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in itemsPagina" :key="t.ID"
              class="border-b border-slate-100 dark:border-slate-800 hover:brightness-95 transition-all"
              :class="t.COLOR ? 'fila-coloreada' : 'dark:hover:brightness-110'"
              :style="t.COLOR ? { backgroundColor: t.COLOR } : {}"
            >
              <!-- Color de la fila: el boton solo abre el menu, el menu en si
              vive fuera de la tabla (ver Teleport al final del template). -->
              <td class="px-2 py-2.5" @click.stop>
                <button
                  @click="toggleMenuColor(t, $event)"
                  :disabled="guardandoColor === t.ID"
                  class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all disabled:opacity-50"
                  :class="t.COLOR ? 'border-white/60 shadow-sm' : 'border-dashed border-slate-300 dark:border-slate-600 hover:border-slate-400'"
                  :style="t.COLOR ? { backgroundColor: t.COLOR } : {}"
                  title="Elegir color"
                >
                  <Palette v-if="!t.COLOR" :size="11" class="text-slate-400" />
                </button>
              </td>
              <td class="px-4 py-2.5">
                <div class="font-semibold text-heading">{{ t.NOMBRE }}</div>
                <div class="text-[11px] text-muted">{{ t.TIPO_DOCUMENTO }} {{ t.DOCUMENTO }}<span v-if="t.EMPRESA"> · {{ t.EMPRESA }}</span></div>
              </td>
              <td class="px-4 py-2.5">
                <span
                  class="text-[11px] font-semibold"
                  :class="t.COLOR
                    ? (t.RENOVADO === 'S' ? 'text-emerald-700' : 'text-[#1d3bd1]')
                    : t.RENOVADO === 'S'
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-[#2447F9] dark:text-blue-400'"
                >{{ t.RENOVADO === 'S' ? 'Renovación' : 'Alta nueva' }}</span>
              </td>
              <td class="px-4 py-2.5">
                <span
                  class="text-[11px] font-semibold"
                  :class="t.COLOR
                    ? (t.ESTADO === 'A' ? 'text-emerald-700' : 'text-red-700')
                    : t.ESTADO === 'A'
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400'"
                >{{ t.ESTADO === 'A' ? 'Activo' : 'Inactivo' }}</span>
              </td>
              <td class="px-4 py-2.5 text-body font-medium">{{ fmtDia(t.FECHA_INGRESO) }}</td>
              <td class="px-4 py-2.5 text-body">{{ fmtDia(t.FECHA_FIN) }}</td>
              <td class="px-4 py-2.5">
                <div class="flex flex-col gap-0.5">
                  <span v-if="t.CORREO" class="inline-flex items-center gap-1.5 text-body"><Mail :size="11" class="text-[#2447F9] shrink-0" /> {{ t.CORREO }}</span>
                  <span v-if="t.TELEFONO" class="inline-flex items-center gap-1.5 text-body"><Phone :size="11" class="text-emerald-600 shrink-0" /> {{ t.TELEFONO }}</span>
                </div>
              </td>
              <td class="px-4 py-2.5 text-body max-w-[220px]">
                <div v-if="t.ULTIMO_CONTACTO_FECHA" class="flex items-start gap-1.5">
                  <MessageSquare :size="11" class="text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div class="text-[11px] text-muted">{{ fmtFechaHora(t.ULTIMO_CONTACTO_FECHA) }}</div>
                    <div class="truncate" :title="t.ULTIMO_CONTACTO_DESC ?? ''">{{ t.ULTIMO_CONTACTO_DESC || '—' }}</div>
                  </div>
                </div>
                <span v-else class="text-muted">Sin seguimiento registrado</span>
              </td>
              <td class="px-4 py-2.5 text-right" @click.stop>
                <button
                  @click="abrirSeguimiento(t)"
                  class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-emerald-50 dark:hover:bg-emerald-950/50 hover:text-emerald-600 dark:hover:text-emerald-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-all ml-auto"
                  title="Registrar seguimiento"
                ><ClipboardList :size="13" /></button>
              </td>
            </tr>
            <tr v-if="!cargando && items.length === 0">
              <td colspan="9" class="px-4 py-12 text-center text-[12px] text-muted">
                {{ mensajeVacio }}
              </td>
            </tr>
            <tr v-if="cargando">
              <td colspan="9" class="px-4 py-12 text-center text-[12px] text-muted">Cargando…</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="totalPaginas > 1" class="flex items-center justify-center gap-3 px-4 py-3 border-t border-slate-200 dark:border-slate-700">
        <button @click="pagina--" :disabled="pagina <= 1"
          class="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all">
          <ChevronLeft :size="15" />
        </button>
        <span class="text-[11px] text-muted">Página <strong class="text-body">{{ pagina }}</strong> de <strong class="text-body">{{ totalPaginas }}</strong></span>
        <button @click="pagina++" :disabled="pagina >= totalPaginas"
          class="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all">
          <ChevronRight :size="15" />
        </button>
      </div>
    </div>

    <SeguimientoDialog v-model:visible="modalSegVisible" :titular="titularSegActual" />

    <!-- Menu de color: teleportado a <body> para quedar siempre por encima de
    la tabla (no como hijo de una celda, donde el scroll horizontal de la
    tabla hacia que otras filas se lo pisaran). El backdrop transparente
    cierra el menu Y bloquea el clic a lo que este debajo mientras esta abierto. -->
    <Teleport to="body">
      <div v-if="itemMenuColor" class="fixed inset-0 z-[9998]" @click="menuColorAbierto = null" />
      <div
        v-if="itemMenuColor"
        class="fixed z-[9999] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-lg p-2.5 w-44"
        :style="{ top: menuColorPos.top + 'px', left: menuColorPos.left + 'px' }"
        @click.stop
      >
        <div class="grid grid-cols-3 gap-2 mb-2">
          <button
            v-for="p in PALETA_COLORES" :key="p.color"
            @click="elegirColor(itemMenuColor, p.color)"
            :title="p.nombre"
            class="w-10 h-10 rounded-lg border border-black/5 hover:scale-105 transition-transform"
            :style="{ backgroundColor: p.color }"
          />
        </div>
        <button
          v-if="itemMenuColor.COLOR"
          @click="elegirColor(itemMenuColor, null)"
          class="w-full flex items-center justify-center gap-1 h-7 rounded-lg border border-slate-200 dark:border-slate-600 text-[10px] font-semibold text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700"
        ><X :size="10" /> Quitar color</button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* La paleta de colores de fila es toda pastel clara: en modo oscuro el texto
claro del tema quedaba ilegible sobre ella, asi que las filas pintadas usan
siempre texto oscuro, sin importar el tema. */
.fila-coloreada .text-heading { color: #0f172a !important; }
.fila-coloreada .text-body { color: #1e293b !important; }
.fila-coloreada .text-muted { color: #475569 !important; }
.fila-coloreada .text-emerald-600 { color: #047857 !important; }
.fila-coloreada .text-slate-400 { color: #64748b !important; }
</style>
