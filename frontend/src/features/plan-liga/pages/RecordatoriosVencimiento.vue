<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import {
  Clock, Mail, RefreshCw, Send, AlertTriangle, CheckCircle2, CalendarClock,
  ChevronLeft, ChevronRight, ChevronDown, User, Building2,
} from 'lucide-vue-next'
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue'
import SeccionColapsable from '@/shared/components/SeccionColapsable.vue'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'
import {
  getPorVencer, enviarRecordatorios, getHistorialEnvios, getEmpresasPorVencer,
  type ListadoPorVencer, type EnvioResultado, type HistorialEnvioItem,
  type ListadoEmpresasPorVencer, type EmpresaPorVencer,
} from '../services/vencimientos.api'

const { ver: puedeVer, gestionar: puedeGestionar } = permisosDeModulo('recordatorios')

// 'inicio' = elegir Particular/Empresa (migas de pan); 'empresa-detalle' solo
// se llega desde 'empresa' al elegir una empresa puntual.
type Vista = 'inicio' | 'particular' | 'empresa' | 'empresa-detalle'
const vista = ref<Vista>('inicio')

const irInicio = () => { vista.value = 'inicio' }
const irParticular = () => { vista.value = 'particular' }
const irEmpresa = () => { vista.value = 'empresa'; empresaSeleccionada.value = null }

// Ventana de días: compartida entre Particular y Empresa (mismo significado
// de negocio en los dos casos).
const diasPrevios = ref(7)
// 0 = no incluir titulares ya vencidos (los de hoy dejan de aparecer mañana).
const diasVencidos = ref(0)

const textoDias = (dias: number) => {
  if (dias < 0) return `Venció hace ${Math.abs(dias)} d`
  if (dias === 0) return 'Vence hoy'
  return `${dias} d`
}
const fmtFecha = (iso: string | null) => {
  if (!iso) return 'Nunca'
  return new Date(iso).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
const fmtDia = (iso: string | null) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
}

/* ------------------------------------------------------------------ */
/* Particular: exactamente el flujo de siempre.                        */
/* ------------------------------------------------------------------ */
const cargando = ref(false)
const enviando = ref(false)
const error = ref<string | null>(null)
const datos = ref<ListadoPorVencer | null>(null)
const resultado = ref<EnvioResultado | null>(null)
const confirmVisible = ref(false)
const historial = ref<HistorialEnvioItem[]>([])

const cargarHistorial = async () => {
  try {
    historial.value = await getHistorialEnvios(20)
  } catch {
    // el historial es informativo; si falla no bloquea el resto de la pantalla
  }
}

const cargar = async () => {
  cargando.value = true
  error.value = null
  try {
    datos.value = await getPorVencer({ diasPrevios: diasPrevios.value, diasVencidos: diasVencidos.value })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo cargar la información.'
  } finally {
    cargando.value = false
  }
}

// 'nuevos' = solo los que aún no recibieron el aviso; 'todos' = reenviar a
// todos los de la ventana (incluye los ya avisados).
const modoEnvio = ref<'nuevos' | 'todos'>('nuevos')

const pedirEnvio = (modo: 'nuevos' | 'todos') => {
  modoEnvio.value = modo
  confirmVisible.value = true
}

const ejecutarEnvio = async () => {
  enviando.value = true
  error.value = null
  resultado.value = null
  try {
    resultado.value = await enviarRecordatorios({
      diasPrevios: diasPrevios.value,
      diasVencidos: diasVencidos.value,
      incluirYaEnviados: modoEnvio.value === 'todos',
    })
    await Promise.all([cargar(), cargarHistorial()])
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudieron enviar los recordatorios.'
  } finally {
    enviando.value = false
  }
}

const items = computed(() => datos.value?.items ?? [])
const totalPendientes = computed(() => datos.value?.total ?? 0)
const nuevos = computed(() => datos.value?.nuevos ?? 0)
const yaEnviados = computed(() => datos.value?.ya_enviados ?? 0)
const estado = computed(() => datos.value?.estado_envio ?? null)
const cubiertoHasta = computed(() => estado.value?.cubierto_hasta ?? null)

// Paginación en cliente (el backend devuelve todo; la ventana de vencimiento
// es acotada, no llega a miles de filas).
const POR_PAGINA = 6
const pagina = ref(1)
const totalPaginas = computed(() => Math.max(1, Math.ceil(items.value.length / POR_PAGINA)))
const itemsPagina = computed(() =>
  items.value.slice((pagina.value - 1) * POR_PAGINA, pagina.value * POR_PAGINA),
)
watch(items, () => { pagina.value = 1 })

// Filas del historial expandibles (para ver el detalle de fallos de esa corrida).
const historialAbierto = ref<number | null>(null)
const toggleHistorial = (i: number) => {
  historialAbierto.value = historialAbierto.value === i ? null : i
}

// Ventana de días como texto corto: "-1 d a +7 d", "solo hoy", "hoy a +7 d"…
const ventanaTxt = (prev: number | null, venc: number | null) => {
  if (prev == null || venc == null) return '—'
  if (prev === 0 && venc === 0) return 'solo hoy'
  const desde = venc === 0 ? 'hoy' : `-${venc} d`
  const hasta = prev === 0 ? 'hoy' : `+${prev} d`
  return `${desde} a ${hasta}`
}

const mensajeConfirmar = computed(() => {
  if (modoEnvio.value === 'todos') {
    return `Se REENVIARÁ el correo a los ${totalPendientes.value} titular(es) particular(es) de la ventana, incluidos los ${yaEnviados.value} que ya lo recibieron antes. Algunos recibirán el correo dos veces. ¿Continuar?`
  }
  return `Se enviará el correo a ${nuevos.value} titular(es) particular(es) que aún no lo han recibido. Los ${yaEnviados.value} ya avisados no se tocan. ¿Continuar?`
})

/* ------------------------------------------------------------------ */
/* Empresa: solo consulta. Se muestra qué empresas tienen titulares    */
/* por vencer; NO se envían correos desde aquí.                        */
/* ------------------------------------------------------------------ */
const cargandoEmpresas = ref(false)
const errorEmpresas = ref<string | null>(null)
const datosEmpresas = ref<ListadoEmpresasPorVencer | null>(null)
const empresas = computed(() => datosEmpresas.value?.empresas ?? [])

const cargarEmpresas = async () => {
  cargandoEmpresas.value = true
  errorEmpresas.value = null
  try {
    datosEmpresas.value = await getEmpresasPorVencer({ diasPrevios: diasPrevios.value, diasVencidos: diasVencidos.value })
  } catch (e) {
    errorEmpresas.value = e instanceof Error ? e.message : 'No se pudo cargar la lista de empresas.'
  } finally {
    cargandoEmpresas.value = false
  }
}

const empresaSeleccionada = ref<EmpresaPorVencer | null>(null)
const abrirEmpresa = (e: EmpresaPorVencer) => {
  empresaSeleccionada.value = e
  vista.value = 'empresa-detalle'
}

watch(vista, (v) => {
  if (v === 'empresa' && !datosEmpresas.value) cargarEmpresas()
})

onMounted(() => {
  cargar()
  cargarHistorial()
})
</script>

<template>
  <div v-if="!puedeVer" class="surface-card rounded-2xl shadow-sm text-center py-16">
    <AlertTriangle :size="28" class="text-slate-300 dark:text-slate-600 mx-auto mb-3" />
    <p class="text-[13px] font-semibold text-subtle">Sin acceso a este módulo</p>
  </div>

  <div v-else class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div>
      <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
        <CalendarClock :size="20" class="text-[#C9A227]" />
        Recordatorios de vencimiento · Plan Liga
      </h2>
      <!-- Migas de pan -->
      <nav class="flex items-center gap-1.5 text-[12px] mt-1">
        <button
          @click="irInicio"
          class="font-semibold hover:text-[#2447F9] transition-colors"
          :class="vista === 'inicio' ? 'text-heading' : 'text-muted'"
        >Elegir segmento</button>
        <template v-if="vista !== 'inicio'">
          <ChevronRight :size="12" class="text-muted" />
          <button
            @click="vista = vista === 'empresa-detalle' ? 'empresa' : vista"
            class="font-semibold hover:text-[#2447F9] transition-colors"
            :class="vista === 'particular' || vista === 'empresa' ? 'text-heading' : 'text-muted'"
          >{{ vista === 'particular' ? 'Particular' : 'Empresa' }}</button>
        </template>
        <template v-if="vista === 'empresa-detalle' && empresaSeleccionada">
          <ChevronRight :size="12" class="text-muted" />
          <span class="font-semibold text-heading">{{ empresaSeleccionada.EMPRESA }}</span>
        </template>
      </nav>
    </div>

    <!-- ============ INICIO: elegir Particular / Empresa ============ -->
    <div v-if="vista === 'inicio'" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <button
        @click="irParticular"
        class="surface-card rounded-2xl shadow-sm p-6 text-left hover:shadow-md hover:-translate-y-0.5 transition-all"
      >
        <div class="w-11 h-11 rounded-xl bg-[#EEF2FF] dark:bg-blue-950/50 flex items-center justify-center mb-4">
          <User :size="20" class="text-[#2447F9] dark:text-blue-400" />
        </div>
        <h3 class="text-[14px] font-bold text-heading mb-1">Particular</h3>
        <p class="text-[12px] text-muted leading-relaxed">
          Titulares individuales, sin empresa asociada. Desde aquí se les
          <strong>envía el correo</strong> de recordatorio a su propio correo.
        </p>
      </button>
      <button
        @click="irEmpresa"
        class="surface-card rounded-2xl shadow-sm p-6 text-left hover:shadow-md hover:-translate-y-0.5 transition-all"
      >
        <div class="w-11 h-11 rounded-xl bg-[#FCE7F3] dark:bg-pink-950/40 flex items-center justify-center mb-4">
          <Building2 :size="20" class="text-[#EC4899] dark:text-pink-300" />
        </div>
        <h3 class="text-[14px] font-bold text-heading mb-1">Empresa</h3>
        <p class="text-[12px] text-muted leading-relaxed">
          Titulares de un convenio Plan Liga Empresarial, agrupados por empresa.
          <strong>Solo consulta</strong>: no se envían correos desde aquí.
        </p>
      </button>
    </div>

    <!-- ============ PARTICULAR ============ -->
    <template v-if="vista === 'particular'">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <p class="text-[12px] text-body">
          Titulares particulares con la membresía próxima a vencer. Excluye plan LIGA (empleados) y a los de empresa.
        </p>
        <div class="flex items-center gap-2">
          <button
            @click="cargar"
            :disabled="cargando"
            class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all disabled:opacity-50"
          >
            <RefreshCw :size="13" :class="cargando ? 'animate-spin' : ''" /> Actualizar
          </button>
          <button
            v-if="puedeGestionar"
            @click="pedirEnvio('nuevos')"
            :disabled="enviando || nuevos === 0"
            class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50"
          >
            <Send :size="14" /> {{ enviando ? 'Enviando…' : `Enviar nuevos (${nuevos})` }}
          </button>
          <button
            v-if="puedeGestionar && yaEnviados > 0"
            @click="pedirEnvio('todos')"
            :disabled="enviando"
            class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 text-[11px] font-bold text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-950/60 transition-all disabled:opacity-50"
          >
            <Send :size="13" /> Reenviar todos ({{ totalPendientes }})
          </button>
        </div>
      </div>

      <!-- Ventana de días -->
      <div class="surface-card rounded-2xl shadow-sm px-4 py-3 flex flex-wrap items-end gap-4">
        <label class="text-[11px] font-semibold text-subtle uppercase tracking-wide">
          Días antes de vencer
          <input v-model.number="diasPrevios" type="number" min="0" max="60"
            class="mt-1 block w-24 h-9 px-3 rounded-lg input-surface text-[12px] outline-none" />
        </label>
        <label class="text-[11px] font-semibold text-subtle uppercase tracking-wide">
          Días ya vencido
          <input v-model.number="diasVencidos" type="number" min="0" max="30"
            class="mt-1 block w-24 h-9 px-3 rounded-lg input-surface text-[12px] outline-none" />
        </label>
        <button
          @click="cargar"
          class="h-9 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        >Aplicar</button>
        <p class="w-full text-[10px] text-muted">
          Con "Días ya vencido" en <strong>0</strong>, los titulares que ya vencieron dejan de aparecer y de contarse al día siguiente.
        </p>
      </div>

      <!-- Estado del último envío -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="surface-card rounded-2xl shadow-sm p-5">
          <div class="w-9 h-9 rounded-xl bg-[#EEF2FF] dark:bg-blue-950/50 flex items-center justify-center mb-3">
            <Mail :size="17" class="text-[#2447F9] dark:text-blue-400" />
          </div>
          <div class="text-[28px] font-bold text-heading leading-none">
            {{ nuevos }}<span class="text-[15px] text-muted"> / {{ totalPendientes }}</span>
          </div>
          <div class="text-[11px] font-semibold text-subtle uppercase tracking-wide mt-1">
            Nuevos por enviar <span class="text-muted normal-case">({{ yaEnviados }} ya avisados)</span>
          </div>
        </div>
        <div class="surface-card rounded-2xl shadow-sm p-5">
          <div class="w-9 h-9 rounded-xl bg-[#D1FAE5] dark:bg-emerald-950/50 flex items-center justify-center mb-3">
            <Clock :size="17" class="text-[#059669] dark:text-emerald-400" />
          </div>
          <div class="text-[15px] font-bold text-heading leading-tight">{{ fmtFecha(estado?.ultimo_envio ?? null) }}</div>
          <div class="text-[11px] font-semibold text-subtle uppercase tracking-wide mt-1">Último envío</div>
          <div v-if="estado?.ejecutado_por" class="text-[11px] text-muted mt-0.5">por {{ estado.ejecutado_por }}</div>
        </div>
        <div class="surface-card rounded-2xl shadow-sm p-5">
          <div class="w-9 h-9 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
            <CheckCircle2 :size="17" class="text-slate-500 dark:text-slate-400" />
          </div>
          <div class="text-[15px] font-bold text-heading leading-tight">
            <template v-if="estado?.ultimo_total != null">
              {{ estado.ultimo_enviados ?? 0 }} / {{ estado.ultimo_total }}
              <span v-if="estado.ultimo_fallidos" class="text-red-500">· {{ estado.ultimo_fallidos }} fallidos</span>
            </template>
            <template v-else>—</template>
          </div>
          <div class="text-[11px] font-semibold text-subtle uppercase tracking-wide mt-1">Resultado última corrida</div>
        </div>
      </div>

      <div v-if="cubiertoHasta" class="rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-[12px] text-amber-700 dark:text-amber-300">
        Ya se enviaron recordatorios a los titulares que vencen
        <strong>hasta el {{ fmtDia(cubiertoHasta) }}</strong>.
        Esos no se reenvían: "Enviar nuevos" solo manda a los que vencen después.
      </div>

      <div v-if="error" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">
        {{ error }}
      </div>

      <div v-if="resultado" class="rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 px-4 py-3 text-[12px] text-emerald-700 dark:text-emerald-300">
        Envío completado: <strong>{{ resultado.enviados }}</strong> enviados de {{ resultado.a_enviar }}.
        <span v-if="resultado.omitidos_ya_enviados"> ({{ resultado.omitidos_ya_enviados }} omitidos por estar ya avisados.)</span>
        <span v-if="resultado.fallidos"> <strong class="text-red-600 dark:text-red-400">{{ resultado.fallidos }} fallidos</strong>
          ({{ resultado.fallos.map(f => f.CORREO).filter(Boolean).join(', ') }}).</span>
      </div>

      <!-- Tabla -->
      <SeccionColapsable
        titulo="Próximos a vencer"
        :subtitulo="`${items.length} titular(es) en esta ventana`"
      >
      <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="px-4 py-2.5 border-b border-slate-200 dark:border-slate-700 text-[11px] text-muted">
          Mostrando <strong class="text-body">{{ itemsPagina.length }}</strong> de
          <strong class="text-body">{{ items.length }}</strong> titulares
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-[12px]">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700 text-left text-[11px] uppercase tracking-wide text-subtle">
                <th class="px-4 py-3 font-semibold">Titular</th>
                <th class="px-4 py-3 font-semibold">Documento</th>
                <th class="px-4 py-3 font-semibold">Correo</th>
                <th class="px-4 py-3 font-semibold">Plan</th>
                <th class="px-4 py-3 font-semibold">Vence</th>
                <th class="px-4 py-3 font-semibold">Faltan</th>
                <th class="px-4 py-3 font-semibold">Aviso</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in itemsPagina" :key="t.ID"
                class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                :class="t.YA_ENVIADO ? 'opacity-70' : ''">
                <td class="px-4 py-2.5 font-semibold text-heading">{{ t.NOMBRE }}</td>
                <td class="px-4 py-2.5 text-body">{{ t.TIPO }} {{ t.DOCUMENTO }}</td>
                <td class="px-4 py-2.5 text-body">{{ t.CORREO }}</td>
                <td class="px-4 py-2.5 text-body">{{ t.TIPO_PLAN || '—' }}</td>
                <td class="px-4 py-2.5 text-body font-medium">{{ t.FECHA_FIN_TXT }}</td>
                <td class="px-4 py-2.5">
                  <span
                    class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold"
                    :class="t.VENCIDO
                      ? 'bg-red-50 text-red-600 dark:bg-red-950/50 dark:text-red-400'
                      : (t.DIAS <= 2
                        ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300')"
                  >{{ textoDias(t.DIAS) }}</span>
                </td>
                <td class="px-4 py-2.5">
                  <span v-if="t.YA_ENVIADO" class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">Ya enviado</span>
                  <span v-else class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-slate-900 dark:bg-blue-950/50 dark:text-white">Pendiente</span>
                </td>
              </tr>
              <tr v-if="!cargando && items.length === 0">
                <td colspan="7" class="px-4 py-12 text-center text-[12px] text-muted">
                  No hay titulares particulares próximos a vencer en esta ventana.
                </td>
              </tr>
              <tr v-if="cargando">
                <td colspan="7" class="px-4 py-12 text-center text-[12px] text-muted">Cargando…</td>
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
      </SeccionColapsable>

      <!-- Historial de corridas -->
      <SeccionColapsable titulo="Historial de envíos" :abierto-por-defecto="false">
      <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-[12px]">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700 text-left text-[11px] uppercase tracking-wide text-subtle">
                <th class="px-4 py-3 font-semibold w-8"></th>
                <th class="px-4 py-3 font-semibold">Fecha</th>
                <th class="px-4 py-3 font-semibold">Ejecutado por</th>
                <th class="px-4 py-3 font-semibold">Ventana</th>
                <th class="px-4 py-3 font-semibold">Enviados</th>
                <th class="px-4 py-3 font-semibold">Fallidos</th>
                <th class="px-4 py-3 font-semibold">Total</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(h, i) in historial" :key="i">
                <tr
                  class="border-b border-slate-100 dark:border-slate-800"
                  :class="h.fallidos ? 'cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50' : ''"
                  @click="h.fallidos && toggleHistorial(i)"
                >
                  <td class="px-4 py-2.5 text-muted">
                    <ChevronDown v-if="h.fallidos" :size="14"
                      class="transition-transform" :class="historialAbierto === i ? 'rotate-180' : ''" />
                  </td>
                  <td class="px-4 py-2.5 text-body font-medium">{{ fmtFecha(h.fecha) }}</td>
                  <td class="px-4 py-2.5 text-body">{{ h.ejecutado_por || '—' }}</td>
                  <td class="px-4 py-2.5 text-body">{{ ventanaTxt(h.dias_previos, h.dias_vencidos) }}</td>
                  <td class="px-4 py-2.5 text-emerald-600 dark:text-emerald-400 font-semibold">{{ h.enviados }}</td>
                  <td class="px-4 py-2.5" :class="h.fallidos ? 'text-red-500 font-semibold' : 'text-body'">{{ h.fallidos }}</td>
                  <td class="px-4 py-2.5 text-body">{{ h.total }}</td>
                </tr>
                <tr v-if="historialAbierto === i && h.fallos.length" class="bg-slate-50 dark:bg-slate-800/40">
                  <td colspan="7" class="px-4 py-3">
                    <p class="text-[11px] font-semibold text-subtle uppercase tracking-wide mb-2">Correos que fallaron</p>
                    <ul class="space-y-1">
                      <li v-for="(f, j) in h.fallos" :key="j" class="text-[11px] text-body">
                        <span class="font-medium">{{ f.NOMBRE || f.DOCUMENTO }}</span>
                        <span class="text-muted"> · {{ f.CORREO }}</span>
                        <span class="text-red-500 dark:text-red-400"> — {{ f.error }}</span>
                      </li>
                    </ul>
                  </td>
                </tr>
              </template>
              <tr v-if="historial.length === 0">
                <td colspan="7" class="px-4 py-10 text-center text-[12px] text-muted">
                  Todavía no se ha ejecutado ningún envío.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      </SeccionColapsable>

      <ConfirmDialog
        v-model:visible="confirmVisible"
        titulo="Enviar recordatorios de vencimiento"
        :mensaje="mensajeConfirmar"
        texto-confirmar="Enviar"
        texto-cancelar="Cancelar"
        @confirmar="ejecutarEnvio"
      />
    </template>

    <!-- ============ EMPRESA: lista agrupada ============ -->
    <template v-if="vista === 'empresa'">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <p class="text-[12px] text-body">
          Empresas con convenio Plan Liga Empresarial que tienen titulares próximos a vencer.
          Vista solo de consulta: <strong>no se envían correos</strong> a las empresas desde el CRM.
        </p>
        <button
          @click="cargarEmpresas"
          :disabled="cargandoEmpresas"
          class="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all disabled:opacity-50 shrink-0"
        >
          <RefreshCw :size="13" :class="cargandoEmpresas ? 'animate-spin' : ''" /> Actualizar
        </button>
      </div>

      <!-- Ventana de días (misma que Particular) -->
      <div class="surface-card rounded-2xl shadow-sm px-4 py-3 flex flex-wrap items-end gap-4">
        <label class="text-[11px] font-semibold text-subtle uppercase tracking-wide">
          Días antes de vencer
          <input v-model.number="diasPrevios" type="number" min="0" max="60"
            class="mt-1 block w-24 h-9 px-3 rounded-lg input-surface text-[12px] outline-none" />
        </label>
        <label class="text-[11px] font-semibold text-subtle uppercase tracking-wide">
          Días ya vencido
          <input v-model.number="diasVencidos" type="number" min="0" max="30"
            class="mt-1 block w-24 h-9 px-3 rounded-lg input-surface text-[12px] outline-none" />
        </label>
        <button
          @click="cargarEmpresas"
          class="h-9 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        >Aplicar</button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="surface-card rounded-2xl shadow-sm p-5">
          <div class="w-9 h-9 rounded-xl bg-[#FCE7F3] dark:bg-pink-950/40 flex items-center justify-center mb-3">
            <Building2 :size="17" class="text-[#EC4899] dark:text-pink-300" />
          </div>
          <div class="text-[28px] font-bold text-heading leading-none">{{ datosEmpresas?.total_empresas ?? 0 }}</div>
          <div class="text-[11px] font-semibold text-subtle uppercase tracking-wide mt-1">Empresas con vencimientos</div>
        </div>
        <div class="surface-card rounded-2xl shadow-sm p-5">
          <div class="w-9 h-9 rounded-xl bg-[#EEF2FF] dark:bg-blue-950/50 flex items-center justify-center mb-3">
            <User :size="17" class="text-[#2447F9] dark:text-blue-400" />
          </div>
          <div class="text-[28px] font-bold text-heading leading-none">{{ datosEmpresas?.total_titulares ?? 0 }}</div>
          <div class="text-[11px] font-semibold text-subtle uppercase tracking-wide mt-1">Colaboradores por vencer</div>
        </div>
      </div>

      <div v-if="errorEmpresas" class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-[12px] text-red-600 dark:text-red-400">
        {{ errorEmpresas }}
      </div>

      <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-[12px]">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700 text-left text-[11px] uppercase tracking-wide text-subtle">
                <th class="px-4 py-3 font-semibold">Empresa</th>
                <th class="px-4 py-3 font-semibold">Colaboradores por vencer</th>
                <th class="px-4 py-3 font-semibold">Vence más pronto</th>
                <th class="px-4 py-3 font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in empresas" :key="e.EMPRESA"
                class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer"
                @click="abrirEmpresa(e)"
              >
                <td class="px-4 py-2.5 font-semibold text-heading">{{ e.EMPRESA }}</td>
                <td class="px-4 py-2.5 text-body">{{ e.TOTAL }}</td>
                <td class="px-4 py-2.5">
                  <span
                    v-if="e.titulares[0]"
                    class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold"
                    :class="e.titulares[0].VENCIDO
                      ? 'bg-red-50 text-red-600 dark:bg-red-950/50 dark:text-red-400'
                      : (e.titulares[0].DIAS <= 2
                        ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300')"
                  >{{ textoDias(e.titulares[0].DIAS) }} · {{ e.titulares[0].FECHA_FIN_TXT }}</span>
                </td>
                <td class="px-4 py-2.5 text-right">
                  <span class="text-[11px] font-bold text-slate-900 dark:text-white">Ver detalle →</span>
                </td>
              </tr>
              <tr v-if="!cargandoEmpresas && empresas.length === 0">
                <td colspan="4" class="px-4 py-12 text-center text-[12px] text-muted">
                  No hay empresas con titulares próximos a vencer en esta ventana.
                </td>
              </tr>
              <tr v-if="cargandoEmpresas">
                <td colspan="4" class="px-4 py-12 text-center text-[12px] text-muted">Cargando…</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- ============ EMPRESA: detalle (solo consulta) ============ -->
    <template v-if="vista === 'empresa-detalle' && empresaSeleccionada">
      <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between gap-3">
          <div>
            <h3 class="text-[13px] font-bold text-heading">{{ empresaSeleccionada.EMPRESA }}</h3>
            <p class="text-[11px] text-muted">{{ empresaSeleccionada.TOTAL }} colaborador(es) por vencer en esta ventana</p>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-[12px]">
            <thead>
              <tr class="border-b border-slate-200 dark:border-slate-700 text-left text-[11px] uppercase tracking-wide text-subtle">
                <th class="px-4 py-3 font-semibold">Titular</th>
                <th class="px-4 py-3 font-semibold">Documento</th>
                <th class="px-4 py-3 font-semibold">Plan</th>
                <th class="px-4 py-3 font-semibold">Vence</th>
                <th class="px-4 py-3 font-semibold">Faltan</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in empresaSeleccionada.titulares" :key="t.ID" class="border-b border-slate-100 dark:border-slate-800">
                <td class="px-4 py-2.5 font-semibold text-heading">{{ t.NOMBRE }}</td>
                <td class="px-4 py-2.5 text-body">{{ t.TIPO }} {{ t.DOCUMENTO }}</td>
                <td class="px-4 py-2.5 text-body">{{ t.TIPO_PLAN || '—' }}</td>
                <td class="px-4 py-2.5 text-body font-medium">{{ t.FECHA_FIN_TXT }}</td>
                <td class="px-4 py-2.5">
                  <span
                    class="inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold"
                    :class="t.VENCIDO
                      ? 'bg-red-50 text-red-600 dark:bg-red-950/50 dark:text-red-400'
                      : (t.DIAS <= 2
                        ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300')"
                  >{{ textoDias(t.DIAS) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
