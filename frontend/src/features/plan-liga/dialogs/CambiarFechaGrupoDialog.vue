<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, CalendarClock, Loader2, CheckCircle2, AlertTriangle } from 'lucide-vue-next'
import DatePicker from 'primevue/datepicker'
import { contarGrupoActivo, cambiarFechaIngresoGrupo, getTiposPlan, type GrupoRef } from '../services/plan-liga.api'
import { getEmpresas } from '@/features/empresas/services/empresas.api'
import type { Empresa } from '@/features/empresas/types/empresa'
import BuscadorEntidad, { type OpcionBuscador } from '@/shared/components/BuscadorEntidad.vue'

const visible = defineModel<boolean>('visible', { required: true })

const empresas = ref<Empresa[]>([])
const tiposPlan = ref<string[]>([])
const cargandoEmpresas = ref(false)
const seleccionId = ref<number | null>(null)

// Las empresas usan su id real (positivo); los tipos de plan no tienen un id
// propio, asi que se les da uno sintetico negativo (-(indice+1)) para poder
// convivir en el mismo buscador sin chocar con los ids reales de empresa.
const opcionesEmpresas = computed<OpcionBuscador[]>(() => [
  ...empresas.value.map(e => ({ id: e.id, label: e.razonSocial, sublabel: e.ciudad })),
  ...tiposPlan.value.map((tp, i) => ({ id: -(i + 1), label: tp, sublabel: 'Tipo de plan' })),
])

const grupoSeleccionado = computed<GrupoRef | null>(() => {
  if (seleccionId.value === null) return null
  if (seleccionId.value < 0) {
    const tipoPlan = tiposPlan.value[-seleccionId.value - 1]
    return tipoPlan ? { tipoPlan } : null
  }
  const empresa = empresas.value.find(e => e.id === seleccionId.value)?.razonSocial
  return empresa ? { empresa } : null
})
// Nombre a mostrar en el texto de confirmación/resultado (sirve para los dos casos).
const nombreGrupoSeleccionado = computed(() => grupoSeleccionado.value?.empresa ?? grupoSeleccionado.value?.tipoPlan ?? '')
const fechaDate = ref<Date>(new Date())
const error = ref<string | null>(null)
const resultado = ref<{ titularesActualizados: number; beneficiariosActualizados: number } | null>(null)

// Paso intermedio: antes de aplicar el cambio se cuenta cuántos titulares/beneficiarios
// activos se verían afectados y se pide confirmación explícita con esos números.
const confirmando = ref(false)
const cargandoConteo = ref(false)
const guardando = ref(false)
const conteoPreview = ref<{ titulares: number; beneficiarios: number } | null>(null)

const formatFechaLocal = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const formatFechaDisplay = (d: Date) => `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`

watch(visible, async (v) => {
  if (!v) return
  seleccionId.value = null
  fechaDate.value = new Date()
  error.value = null
  resultado.value = null
  confirmando.value = false
  conteoPreview.value = null
  cargandoEmpresas.value = true
  // allSettled, no all: si "tipos de plan" falla (ej. backend viejo sin ese
  // endpoint todavia), las empresas se siguen mostrando igual -- con Promise.all
  // un solo fallo dejaba las DOS listas vacias, sin avisar por qué.
  const [empresasResult, tiposPlanResult] = await Promise.allSettled([getEmpresas(), getTiposPlan()])
  empresas.value = empresasResult.status === 'fulfilled' ? empresasResult.value : []
  tiposPlan.value = tiposPlanResult.status === 'fulfilled' ? tiposPlanResult.value : []
  const fallos = [empresasResult, tiposPlanResult].filter(r => r.status === 'rejected') as PromiseRejectedResult[]
  if (fallos.length) {
    error.value = fallos
      .map(r => (r.reason instanceof Error ? r.reason.message : String(r.reason)))
      .join(' · ')
  }
  cargandoEmpresas.value = false
})

const cerrar = () => { visible.value = false }

const pedirConfirmacion = async () => {
  if (!grupoSeleccionado.value) {
    error.value = 'Elige una empresa, grupo o tipo de plan.'
    return
  }
  error.value = null
  cargandoConteo.value = true
  try {
    const conteo = await contarGrupoActivo(grupoSeleccionado.value)
    conteoPreview.value = { titulares: conteo.titularesActualizados, beneficiarios: conteo.beneficiariosActualizados }
    confirmando.value = true
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo calcular cuántos registros se verían afectados.'
  } finally {
    cargandoConteo.value = false
  }
}

const cancelarConfirmacion = () => {
  confirmando.value = false
  conteoPreview.value = null
}

const aplicarCambio = async () => {
  if (!grupoSeleccionado.value) return
  error.value = null
  guardando.value = true
  try {
    resultado.value = await cambiarFechaIngresoGrupo(grupoSeleccionado.value, formatFechaLocal(fechaDate.value))
    confirmando.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo cambiar la fecha de ingreso del grupo.'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-sm flex flex-col">
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-[#F8FAFC] dark:bg-slate-900 rounded-t-2xl">
        <div>
          <h3 class="text-[14px] font-bold text-[#0F172A] dark:text-slate-100 flex items-center gap-2">
            <CalendarClock :size="15" class="text-[#2447F9]" />Cambiar fecha de ingreso por grupo
          </h3>
          <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Aplica a todos los titulares y beneficiarios activos de la empresa o grupo elegido</p>
        </div>
        <button @click="cerrar" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-4">
        <template v-if="!confirmando && !resultado">
          <div>
            <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Empresa / grupo / tipo de plan *</label>
            <BuscadorEntidad
              v-model="seleccionId"
              :opciones="opcionesEmpresas"
              :disabled="cargandoEmpresas"
              :placeholder="cargandoEmpresas ? 'Cargando...' : 'Busca por empresa, grupo o tipo de plan'"
              vacio="No se encontraron empresas, grupos ni tipos de plan"
            />
          </div>

          <div>
            <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Nueva fecha de ingreso *</label>
            <DatePicker
              v-model="fechaDate"
              date-format="dd/mm/yy"
              show-icon
              icon-display="input"
              fluid
              placeholder="Selecciona una fecha"
              input-class="w-full h-11 pl-4 pr-10 rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] font-medium text-slate-700 dark:text-slate-100 outline-none focus:border-[#2447F9] focus:ring-4 focus:ring-blue-50 dark:focus:ring-blue-900/40 focus:bg-white dark:focus:bg-slate-800 transition-all"
            />
          </div>
        </template>

        <div v-if="confirmando && !resultado" class="flex items-start gap-2 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl px-3 py-2.5">
          <AlertTriangle :size="15" class="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <p class="text-[12px] text-amber-800 dark:text-amber-300 font-medium">
            Vas a cambiar la fecha de ingreso a <strong>{{ formatFechaDisplay(fechaDate) }}</strong> de
            <strong>{{ conteoPreview?.titulares ?? 0 }}</strong> titular{{ conteoPreview?.titulares === 1 ? '' : 'es' }}
            y <strong>{{ conteoPreview?.beneficiarios ?? 0 }}</strong> beneficiario{{ conteoPreview?.beneficiarios === 1 ? '' : 's' }}
            de <strong>{{ nombreGrupoSeleccionado }}</strong>. ¿Confirmas?
          </p>
        </div>

        <p v-if="error" class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>

        <div v-if="resultado" class="flex items-start gap-2 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl px-3 py-2.5">
          <CheckCircle2 :size="15" class="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <p class="text-[11px] text-emerald-700 dark:text-emerald-300 font-medium">
            Actualizados {{ resultado.titularesActualizados }} titular{{ resultado.titularesActualizados === 1 ? '' : 'es' }}
            y {{ resultado.beneficiariosActualizados }} beneficiario{{ resultado.beneficiariosActualizados === 1 ? '' : 's' }}.
          </p>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-[#F8FAFC] dark:bg-slate-900 rounded-b-2xl">
        <button
          v-if="resultado"
          @click="cerrar"
          class="h-9 px-5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
        >
          Cerrar
        </button>
        <template v-else-if="confirmando">
          <button
            @click="cancelarConfirmacion"
            :disabled="guardando"
            class="h-9 px-5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-60 transition-all"
          >
            Cancelar
          </button>
          <button
            @click="aplicarCambio"
            :disabled="guardando"
            class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] disabled:opacity-60 disabled:cursor-not-allowed transition-all"
          >
            <Loader2 v-if="guardando" :size="12" class="animate-spin" />
            Aceptar
          </button>
        </template>
        <template v-else>
          <button @click="cerrar" class="h-9 px-5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
            Cancelar
          </button>
          <button
            @click="pedirConfirmacion"
            :disabled="cargandoConteo"
            class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] disabled:opacity-60 disabled:cursor-not-allowed transition-all"
          >
            <Loader2 v-if="cargandoConteo" :size="12" class="animate-spin" />
            Aplicar cambio
          </button>
        </template>
      </div>
    </div>
  </div>
</template>
