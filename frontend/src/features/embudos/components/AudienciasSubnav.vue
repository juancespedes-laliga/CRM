<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { SlidersHorizontal, UsersRound } from 'lucide-vue-next'

// Sub-vistas de Audiencias: la audiencia armada con filtros (se recalcula) y los
// grupos de interés (listas fijas). Se muestra arriba en las dos páginas.
const SUBVISTAS = [
  { ruta: '/embudos/afiliado', label: 'Por filtros', icono: SlidersHorizontal },
  { ruta: '/embudos/afiliado/grupos', label: 'Grupos de interés', icono: UsersRound },
]

const route = useRoute()
const router = useRouter()
</script>

<template>
  <nav class="flex items-center gap-1 border-b border-default" aria-label="Sub-vistas de Audiencias">
    <button
      v-for="s in SUBVISTAS"
      :key="s.ruta"
      type="button"
      @click="route.path !== s.ruta && router.push(s.ruta)"
      class="flex items-center gap-1.5 h-9 px-3 -mb-px border-b-2 text-[12px] font-semibold transition-colors"
      :class="route.path === s.ruta
        ? 'border-[#2447F9] text-slate-900 font-bold dark:text-white dark:border-blue-300'
        : 'border-transparent text-muted hover:text-heading'"
    >
      <component :is="s.icono" :size="13" /> {{ s.label }}
    </button>
  </nav>
</template>
