<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { BarChart3, FileCode2, Megaphone } from 'lucide-vue-next'

// Sub-vistas de Campañas: plantillas del editor del CRM, envíos masivos por
// MailerTurbo y sus estadísticas.
const SUBVISTAS = [
  { ruta: '/campanas', label: 'Plantillas', icono: FileCode2 },
  { ruta: '/campanas/mailerturbo', label: 'MailerTurbo', icono: Megaphone },
  { ruta: '/campanas/estadisticas', label: 'Estadísticas', icono: BarChart3 },
]

const route = useRoute()
const router = useRouter()
// El detalle de una campaña cuelga de la vista desde la que se abrió
// (?desde=estadisticas) o, por defecto, de MailerTurbo.
const activa = (ruta: string) => {
  if (ruta === '/campanas') return route.path === ruta
  if (route.name === 'campanas-mailerturbo-detalle') {
    return ruta === (route.query.desde === 'estadisticas' ? '/campanas/estadisticas' : '/campanas/mailerturbo')
  }
  return route.path.startsWith(ruta)
}
</script>

<template>
  <nav class="flex items-center gap-1 border-b border-default" aria-label="Sub-vistas de Campañas">
    <button
      v-for="s in SUBVISTAS"
      :key="s.ruta"
      type="button"
      @click="route.path !== s.ruta && router.push(s.ruta)"
      :aria-current="activa(s.ruta) ? 'page' : undefined"
      class="flex items-center gap-1.5 h-9 px-3 -mb-px border-b-2 text-[12px] font-semibold transition-colors"
      :class="activa(s.ruta)
        ? 'border-[#2447F9] text-slate-900 font-bold dark:text-white dark:border-blue-300'
        : 'border-transparent text-muted hover:text-heading'"
    >
      <component :is="s.icono" :size="13" /> {{ s.label }}
    </button>
  </nav>
</template>
