<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'
import { HUB_CARDS } from '../constants/hub.constants'
import { useSegmentosGuardados } from '../composables/useSegmentosGuardados'

const router = useRouter()
const nf = new Intl.NumberFormat('es-CO')

const { segmentos } = useSegmentosGuardados()

// Solo la tarjeta de Segmentos guardados tiene un numero real (viene de
// localStorage, es instantaneo). La de Audiencias no muestra ningun dato:
// calcularlo en vivo pegaba contra TMPBI1 (millones de filas) y tardaba
// demasiado para una tarjeta del hub.
const datoReal = computed<Record<string, { dato: string; datoLabel: string }>>(() => ({
  '/segmentos': {
    dato: nf.format(segmentos.value.length),
    datoLabel: 'segmentos activos',
  },
}))
</script>

<template>
  <div class="space-y-6 font-[Inter,system-ui,sans-serif]">
    <!-- Header + breadcrumb -->
    <div>
      <nav class="flex items-center gap-1.5 text-[12px] mb-1.5">
        <span class="text-slate-400 dark:text-slate-500">CRM Mercadeo</span>
        <ChevronRight :size="12" class="text-slate-300 dark:text-slate-600" />
        <span class="font-bold text-[#0F172A] dark:text-slate-100">Embudos</span>
      </nav>
      <h2 class="text-[18px] font-bold text-heading">Embudos y segmentación</h2>
      <p class="text-[12px] text-body mt-0.5">
        Elige una vista para armar una audiencia y actuar sobre ella, o trabajar los segmentos guardados.
      </p>
    </div>

    <!-- Grid de vistas -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <button
        v-for="c in HUB_CARDS"
        :key="c.ruta"
        type="button"
        @click="router.push(c.ruta)"
        class="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-5 text-left hover:shadow-md hover:-translate-y-0.5 transition-all group"
      >
        <div class="flex items-start justify-between mb-4">
          <div class="w-11 h-11 rounded-xl flex items-center justify-center" :style="{ backgroundColor: c.bg }">
            <component :is="c.icono" :size="20" :style="{ color: c.color }" />
          </div>
          <ChevronRight :size="16" class="text-slate-300 dark:text-slate-600 group-hover:text-[#2447F9] group-hover:translate-x-0.5 transition-all" />
        </div>

        <h3 class="text-[14px] font-bold text-heading">{{ c.titulo }}</h3>
        <p class="text-[12px] text-muted mt-1 leading-relaxed">{{ c.descripcion }}</p>

        <div v-if="datoReal[c.ruta]" class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700 flex items-baseline gap-1.5">
          <span class="text-[20px] font-extrabold tabular-nums" :style="{ color: c.color }">{{ datoReal[c.ruta].dato }}</span>
          <span class="text-[11px] text-muted">{{ datoReal[c.ruta].datoLabel }}</span>
        </div>
      </button>
    </div>
  </div>
</template>
