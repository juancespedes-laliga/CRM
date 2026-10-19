<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  FileSpreadsheet, Send, CloudUpload, RefreshCw, Search, Loader2, ListPlus, ExternalLink, Mail, Phone, UserRound, X,
} from 'lucide-vue-next'
import type { InfoContactoMT, ListaMT } from '../types/mailerturbo'
import { abrirMailerTurbo, buscarContacto } from '../services/mailerturbo.api'
import { useCatalogosMailerturbo } from '../composables/useCatalogosMailerturbo'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'
import { descargarPlantillaBaseContactos } from '../utils/baseContactos'
import EnviarCampanaDialog from '../dialogs/EnviarCampanaDialog.vue'
import SubirContactosDialog from '../dialogs/SubirContactosDialog.vue'

// Pestaña "MailerTurbo" de Gestión de Contactos: listas con sus métricas, búsqueda
// de un contacto y el flujo Excel -> campaña. La API de MailerTurbo no permite
// listar los contactos de una lista; solo consultar uno por correo o teléfono.
const { gestionar: puedeGestionar } = permisosDeModulo('contactos')
const nf = new Intl.NumberFormat('es-CO')

const { listas, cargando, error, cargar, nuevaLista } = useCatalogosMailerturbo()
onMounted(() => void cargar())

// ── Resumen ──────────────────────────────────────────────────────────
const listasActivas = computed(() => listas.value.filter(l => l.estado === 'Activa'))
const suma = (campo: keyof Pick<ListaMT, 'totalCorreos' | 'totalActivos' | 'totalRebotes' | 'totalSalidas'>) =>
  listasActivas.value.reduce((s, l) => s + l[campo], 0)
const kpis = computed(() => [
  { label: 'Listas activas', valor: listasActivas.value.length, color: 'text-heading' },
  { label: 'Contactos en listas', valor: suma('totalCorreos'), color: 'text-heading' },
  { label: 'Activos', valor: suma('totalActivos'), color: 'text-emerald-600 dark:text-emerald-400' },
  { label: 'Rebotes', valor: suma('totalRebotes'), color: 'text-amber-600 dark:text-amber-400' },
  { label: 'Bajas', valor: suma('totalSalidas'), color: 'text-red-500 dark:text-red-400' },
])

// ── Listas ───────────────────────────────────────────────────────────
const busquedaLista = ref('')
const verArchivadas = ref(false)
const listasFiltradas = computed(() => {
  const q = busquedaLista.value.trim().toLowerCase()
  return listas.value
    .filter(l => verArchivadas.value || l.estado === 'Activa')
    .filter(l => !q || l.titulo.toLowerCase().includes(q))
})
const pct = (parte: number, total: number) => (total ? `${((parte / total) * 100).toFixed(1)}%` : '—')
const fmtFecha = (f: string | null) => (f ? new Date(f.replace(' ', 'T')).toLocaleDateString('es-CO', { dateStyle: 'medium' }) : '—')

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

// ── Buscar un contacto ───────────────────────────────────────────────
const busquedaContacto = ref('')
const buscando = ref(false)
const contactoEncontrado = ref<InfoContactoMT | null>(null)
const sinResultado = ref(false)
const errorBusqueda = ref<string | null>(null)
async function buscar() {
  const q = busquedaContacto.value.trim()
  if (!q) return
  buscando.value = true
  errorBusqueda.value = null
  sinResultado.value = false
  contactoEncontrado.value = null
  try {
    const esCorreo = q.includes('@')
    contactoEncontrado.value = await buscarContacto(esCorreo ? { correo: q } : { telefono: q })
    sinResultado.value = !contactoEncontrado.value
  } catch (e) {
    errorBusqueda.value = e instanceof Error ? e.message : 'No se pudo buscar el contacto.'
  } finally {
    buscando.value = false
  }
}
const limpiarBusqueda = () => {
  busquedaContacto.value = ''
  contactoEncontrado.value = null
  sinResultado.value = false
  errorBusqueda.value = null
}
const claseEstadoCorreo = (estado: string | null) =>
  estado === 'Activo' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
    : 'bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300'

// ── Abrir la plataforma ya logueado ──────────────────────────────────
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
const campanaVisible = ref(false)
const campanaFuente = ref<'listas' | 'archivo'>('archivo')
const campanaListas = ref<number[]>([])
const abrirCampanaExcel = () => { campanaFuente.value = 'archivo'; campanaListas.value = []; campanaVisible.value = true }
const abrirCampanaLista = (l: ListaMT) => { campanaFuente.value = 'listas'; campanaListas.value = [l.id]; campanaVisible.value = true }

const subirVisible = ref(false)
const subirListaId = ref<number | undefined>(undefined)
const abrirSubir = (l?: ListaMT) => { subirListaId.value = l?.id; subirVisible.value = true }

const PASOS = [
  { n: 1, titulo: 'Sube tu Excel o CSV', texto: 'Columnas NOMBRE, APELLIDO, CORREO y TELEFONO.' },
  { n: 2, titulo: 'Elige contenido y remitente', texto: 'Plantilla de MailerTurbo o del editor del CRM.' },
  { n: 3, titulo: 'Envía o programa', texto: 'MailerTurbo crea la lista y la campaña.' },
]
</script>

<template>
  <div class="space-y-4">
    <!-- Flujo Excel -> campaña -->
    <div v-if="puedeGestionar" class="surface-card rounded-2xl shadow-sm p-5">
      <div class="flex flex-col lg:flex-row lg:items-center gap-5">
        <div class="flex-1 min-w-0">
          <h3 class="text-[14px] font-bold text-heading flex items-center gap-2">
            <FileSpreadsheet :size="16" class="text-emerald-600" /> Enviar correo a un grupo desde Excel
          </h3>
          <ol class="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <li v-for="p in PASOS" :key="p.n" class="flex items-start gap-2.5">
              <span class="w-6 h-6 rounded-full bg-[#EEF2FF] dark:bg-blue-950/50 text-[#2447F9] dark:text-blue-300 text-[11px] font-bold grid place-items-center shrink-0">{{ p.n }}</span>
              <div>
                <div class="text-[12px] font-semibold text-heading">{{ p.titulo }}</div>
                <div class="text-[11px] text-muted">{{ p.texto }}</div>
              </div>
            </li>
          </ol>
        </div>
        <div class="flex flex-col gap-2 shrink-0 lg:w-56">
          <button
            @click="abrirCampanaExcel"
            class="flex items-center justify-center gap-1.5 h-10 px-4 rounded-lg bg-[#2447F9] text-white text-[12px] font-bold shadow hover:bg-[#1D3DD9] transition-all"
          ><Send :size="14" /> Cargar Excel y enviar</button>
          <button
            @click="abrirSubir()"
            class="flex items-center justify-center gap-1.5 h-9 px-4 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
          ><CloudUpload :size="13" /> Solo subir Excel a una lista</button>
          <button type="button" class="text-[11px] font-semibold text-muted hover:text-[#2447F9]" @click="descargarPlantillaBaseContactos">
            Descargar plantilla de Excel
          </button>
        </div>
      </div>
    </div>

    <!-- Resumen -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <div v-for="k in kpis" :key="k.label" class="surface-card rounded-xl shadow-sm px-4 py-3">
        <div class="text-[10px] font-bold text-subtle uppercase tracking-wide">{{ k.label }}</div>
        <div class="text-[20px] font-bold tabular-nums mt-0.5" :class="k.color">
          <Loader2 v-if="cargando && !listas.length" :size="16" class="animate-spin text-muted" />
          <template v-else>{{ nf.format(k.valor) }}</template>
        </div>
      </div>
    </div>

    <div v-if="error" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">{{ error }}</div>

    <div class="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-4 items-start">
      <!-- Listas -->
      <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-default flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 class="text-[13px] font-bold text-heading">Listas de MailerTurbo</h3>
            <p class="text-[11px] text-muted">Grupos de contactos a los que se envían campañas</p>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="cargar(true)"
              :disabled="cargando"
              class="flex items-center gap-1 h-8 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
              title="Volver a consultar MailerTurbo"
            ><RefreshCw :size="12" :class="{ 'animate-spin': cargando }" /> Actualizar</button>
            <button
              v-if="puedeGestionar"
              @click="creandoLista = !creandoLista; errorLista = null"
              class="flex items-center gap-1 h-8 px-2.5 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700"
            ><ListPlus :size="13" /> Nueva lista</button>
          </div>
        </div>

        <div v-if="creandoLista" class="px-4 py-3 border-b border-default flex flex-wrap items-center gap-2">
          <input
            v-model="tituloLista"
            placeholder="Nombre de la lista"
            class="flex-1 min-w-[200px] h-9 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]"
            @keydown.enter="confirmarNuevaLista"
          />
          <button @click="creandoLista = false" class="h-9 px-3 rounded-lg border border-default text-[11px] font-semibold text-body">Cancelar</button>
          <button
            @click="confirmarNuevaLista"
            :disabled="!tituloLista.trim() || guardandoLista"
            class="h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold disabled:opacity-50"
          >{{ guardandoLista ? 'Creando…' : 'Crear' }}</button>
          <p v-if="errorLista" class="w-full text-[11px] text-red-500">{{ errorLista }}</p>
        </div>

        <div class="flex items-center gap-3 px-4 h-10 border-b border-default">
          <Search :size="13" class="text-muted shrink-0" />
          <input v-model="busquedaLista" placeholder="Buscar lista…" class="flex-1 bg-transparent text-[12px] outline-none text-body" />
          <label class="flex items-center gap-1.5 text-[11px] text-muted cursor-pointer shrink-0">
            <input type="checkbox" v-model="verArchivadas" class="w-3.5 h-3.5 accent-[#2447F9]" /> Ver archivadas
          </label>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-[12px]">
            <thead>
              <tr class="border-b border-default text-left text-[10px] uppercase tracking-wide text-subtle">
                <th class="px-4 py-2.5 font-semibold">Lista</th>
                <th class="px-3 py-2.5 font-semibold text-right">Contactos</th>
                <th class="px-3 py-2.5 font-semibold text-right">Activos</th>
                <th class="px-3 py-2.5 font-semibold text-right">Aperturas</th>
                <th class="px-3 py-2.5 font-semibold text-right">Clics</th>
                <th class="px-3 py-2.5 font-semibold text-right">Rebotes / bajas</th>
                <th v-if="puedeGestionar" class="px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              <tr v-if="cargando && !listas.length">
                <td colspan="7" class="px-4 py-10 text-center text-muted"><Loader2 :size="14" class="animate-spin inline mr-1" /> Consultando MailerTurbo…</td>
              </tr>
              <tr
                v-for="l in listasFiltradas" :key="l.id"
                class="border-b border-slate-100 dark:border-slate-800 group"
                :class="{ 'opacity-60': l.estado !== 'Activa' }"
              >
                <td class="px-4 py-2.5 min-w-[200px]">
                  <div class="font-semibold text-heading truncate max-w-[280px]" :title="l.titulo">{{ l.titulo }}</div>
                  <div class="text-[10px] text-muted">#{{ l.id }} · {{ l.estado }} · creada {{ fmtFecha(l.fechaCreacion) }}</div>
                </td>
                <td class="px-3 py-2.5 text-right tabular-nums font-semibold text-heading">{{ nf.format(l.totalCorreos) }}</td>
                <td class="px-3 py-2.5 text-right tabular-nums text-body">{{ nf.format(l.totalActivos) }}</td>
                <td class="px-3 py-2.5 text-right tabular-nums">
                  <div class="text-body">{{ nf.format(l.totalVistas) }}</div>
                  <div class="text-[10px] text-muted">{{ pct(l.totalVistas, l.totalEnvios) }}</div>
                </td>
                <td class="px-3 py-2.5 text-right tabular-nums">
                  <div class="text-body">{{ nf.format(l.totalClicks) }}</div>
                  <div class="text-[10px] text-muted">{{ pct(l.totalClicks, l.totalEnvios) }}</div>
                </td>
                <td class="px-3 py-2.5 text-right tabular-nums text-body whitespace-nowrap">{{ nf.format(l.totalRebotes) }} / {{ nf.format(l.totalSalidas) }}</td>
                <td v-if="puedeGestionar" class="px-3 py-2.5">
                  <div v-if="l.estado === 'Activa'" class="flex items-center justify-end gap-1">
                    <button @click="abrirSubir(l)" title="Subir contactos a esta lista" class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-[#2447F9] transition-all"><CloudUpload :size="13" /></button>
                    <button @click="abrirCampanaLista(l)" title="Enviar campaña a esta lista" class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-[#2447F9] transition-all"><Send :size="13" /></button>
                  </div>
                </td>
              </tr>
              <tr v-if="!cargando && !listasFiltradas.length">
                <td colspan="7" class="px-4 py-10 text-center text-muted">No hay listas.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="space-y-4">
        <!-- Buscar contacto -->
        <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
          <div class="px-4 py-3 border-b border-default">
            <h3 class="text-[13px] font-bold text-heading">Buscar contacto en MailerTurbo</h3>
            <p class="text-[11px] text-muted">Por correo o teléfono: estado del correo y si acepta campañas</p>
          </div>
          <div class="p-4 space-y-3">
            <div class="flex items-center gap-2">
              <div class="flex-1 flex items-center gap-2 h-9 px-3 rounded-lg input-surface">
                <Search :size="13" class="text-muted shrink-0" />
                <input v-model="busquedaContacto" placeholder="correo@dominio.com o 300…" class="flex-1 min-w-0 bg-transparent text-[12px] outline-none text-body" @keydown.enter="buscar" />
                <button v-if="busquedaContacto" type="button" class="text-muted hover:text-heading" @click="limpiarBusqueda"><X :size="12" /></button>
              </div>
              <button
                @click="buscar"
                :disabled="!busquedaContacto.trim() || buscando"
                class="h-9 px-3 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold disabled:opacity-50"
              ><Loader2 v-if="buscando" :size="13" class="animate-spin" /><template v-else>Buscar</template></button>
            </div>

            <p v-if="errorBusqueda" class="text-[11px] text-red-500">{{ errorBusqueda }}</p>
            <p v-else-if="sinResultado" class="text-[11px] text-muted">No existe en MailerTurbo.</p>

            <div v-if="contactoEncontrado" class="rounded-xl border border-default p-3 space-y-2">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full bg-[#EEF2FF] dark:bg-blue-950/50 grid place-items-center shrink-0"><UserRound :size="15" class="text-[#2447F9]" /></div>
                <div class="min-w-0">
                  <div class="text-[12px] font-bold text-heading truncate">{{ [contactoEncontrado.nombre, contactoEncontrado.apellido].filter(Boolean).join(' ') || 'Sin nombre' }}</div>
                  <div class="text-[10px] text-muted">#{{ contactoEncontrado.id }}</div>
                </div>
              </div>
              <div class="flex items-center gap-1.5 text-[11px] text-body"><Phone :size="12" class="text-[#059669]" /> {{ contactoEncontrado.telefono || 'Sin teléfono' }}</div>
              <div v-for="c in contactoEncontrado.correos" :key="c.correo" class="flex items-center gap-1.5 text-[11px]">
                <Mail :size="12" class="text-[#2447F9] shrink-0" />
                <span class="truncate text-body flex-1" :title="c.correo">{{ c.correo }}</span>
                <span class="text-[10px] font-bold px-1.5 py-0.5 rounded" :class="claseEstadoCorreo(c.estado)">{{ c.estado || '—' }}</span>
                <span class="text-[10px] text-muted" :title="'Acepta campañas: ' + (c.enviarCampana || '—')">{{ c.enviarCampana === 'Si' ? 'Acepta' : 'No acepta' }}</span>
              </div>
              <dl v-if="Object.keys(contactoEncontrado.camposDinamicos).length" class="pt-2 border-t border-default grid grid-cols-2 gap-x-2 gap-y-1 text-[10px]">
                <template v-for="(v, k) in contactoEncontrado.camposDinamicos" :key="k">
                  <dt class="text-subtle truncate">{{ k }}</dt><dd class="text-body truncate" :title="v">{{ v || '—' }}</dd>
                </template>
              </dl>
            </div>
          </div>
        </div>

        <!-- Plataforma -->
        <div class="surface-card rounded-2xl shadow-sm p-4 space-y-2">
          <h3 class="text-[13px] font-bold text-heading">Plataforma MailerTurbo</h3>
          <p class="text-[11px] text-muted">Para ver el detalle de cada lista y sus contactos, abre la plataforma con la sesión ya iniciada.</p>
          <button
            @click="abrirPlataforma"
            :disabled="abriendo"
            class="w-full flex items-center justify-center gap-1.5 h-9 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
          ><Loader2 v-if="abriendo" :size="13" class="animate-spin" /><ExternalLink v-else :size="13" /> Abrir MailerTurbo</button>
          <p v-if="errorAbrir" class="text-[11px] text-red-500">{{ errorAbrir }}</p>
        </div>
      </div>
    </div>

    <EnviarCampanaDialog
      v-model:visible="campanaVisible"
      :fuente-inicial="campanaFuente"
      :id-listas-iniciales="campanaListas"
      origen="Gestión de Contactos"
      @enviada="cargar(true)"
    />
    <SubirContactosDialog v-model:visible="subirVisible" :id-lista-inicial="subirListaId" @subido="cargar(true)" />
  </div>
</template>
