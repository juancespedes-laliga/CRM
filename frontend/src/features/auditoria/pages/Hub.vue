<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'
import { getResumenModulos } from '../services/auditoria.api'
import { VISTAS } from '../constants/auditoria.constants'
import type { ModuloSeleccion, ResumenModulo } from '../types/auditoria'
import { formatoFecha, formatoFechaHora } from '../utils/fechas'

const router = useRouter()
const nf = new Intl.NumberFormat('es-CO')

const resumen = ref<ResumenModulo[]>([])
const cargando = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    resumen.value = await getResumenModulos()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo cargar el conteo de cambios.'
  } finally {
    cargando.value = false
  }
})

const porModulo = computed(() => Object.fromEntries(resumen.value.map(r => [r.modulo, r])) as Record<string, ResumenModulo>)
const totalTodos = computed(() => resumen.value.reduce((s, r) => s + r.total, 0))
const ultimoTodos = computed(() =>
  resumen.value.map(r => r.ultimoCambio).filter((f): f is string => !!f).sort().at(-1) ?? null,
)

// Una tarjeta por vista: "Todos", "Plan Liga" (suma titulares + beneficiarios) y cada módulo.
const tarjetas = computed(() => VISTAS.map(v => {
  if (!v.modulos) return { ...v, total: totalTodos.value, ultimo: ultimoTodos.value }
  const filas = v.modulos.map(m => porModulo.value[m]).filter(Boolean)
  return {
    ...v,
    total: filas.reduce((s, r) => s + r.total, 0),
    ultimo: filas.map(r => r.ultimoCambio).filter((f): f is string => !!f).sort().at(-1) ?? null,
  }
}))

const abrir = (m: ModuloSeleccion) => router.push(`/auditoria/${m}`)
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <!-- Header + breadcrumb -->
    <div>
      <nav class="flex items-center gap-1.5 text-[12px] mb-1.5">
        <span class="text-slate-400 dark:text-slate-500">CRM Mercadeo</span>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <span class="font-bold text-[#0F172A] dark:text-slate-100">Auditoría</span>
      </nav>
      <h2 class="text-[18px] font-bold text-heading">Auditoría</h2>
      <p class="text-[12px] text-body mt-0.5">
        Elige el módulo que quieres auditar para ver quién cambió qué, cuándo y desde dónde.
      </p>
      <p v-if="error" class="mt-2 text-[11px] font-medium text-red-500 dark:text-red-400">{{ error }}</p>
    </div>

    <!-- Una tarjeta compacta por módulo (la primera es "Todos"), para que quepan sin hacer scroll -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
      <button
        v-for="t in tarjetas"
        :key="t.key"
        type="button"
        @click="abrir(t.key)"
        class="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-4 text-left hover:shadow-md hover:-translate-y-0.5 transition-all group flex flex-col"
      >
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" :style="{ backgroundColor: t.bg }">
            <component :is="t.icono" :size="16" :style="{ color: t.color }" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">{{ t.grupo }}</p>
            <h3 class="text-[13px] font-bold text-heading truncate mt-0.5">{{ t.label }}</h3>
          </div>
          <ChevronRight :size="14" class="text-slate-300 dark:text-slate-600 group-hover:text-[#2447F9] group-hover:translate-x-0.5 transition-all shrink-0" />
        </div>

        <p class="text-[11px] text-muted mt-2 leading-snug line-clamp-2 flex-1">{{ t.descripcion }}</p>

        <div class="mt-2.5 flex items-baseline justify-between gap-2">
          <div class="flex items-baseline gap-1">
            <span class="text-[16px] font-extrabold tabular-nums" :style="{ color: t.color }">{{ cargando ? '…' : nf.format(t.total) }}</span>
            <span class="text-[10px] text-muted">cambios</span>
          </div>
          <span v-if="t.ultimo" class="text-[9px] text-muted truncate" :title="`Último cambio: ${formatoFechaHora(t.ultimo)}`">
            {{ formatoFecha(t.ultimo) }}
          </span>
        </div>
      </button>
    </div>

    <p v-if="!cargando && ultimoTodos" class="text-[11px] text-muted">Último cambio registrado: {{ formatoFechaHora(ultimoTodos) }}</p>
  </div>
</template>
