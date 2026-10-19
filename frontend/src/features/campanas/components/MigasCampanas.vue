<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'

// Migas de pan de la sección Campañas: "Campañas › MailerTurbo › <campaña>".
// El último elemento es la página actual (sin enlace).
export interface Miga { label: string; ruta?: string }
defineProps<{ migas: Miga[] }>()
const router = useRouter()
</script>

<template>
  <nav class="flex items-center gap-1.5 text-[12px] min-w-0" aria-label="Migas de pan">
    <template v-for="(m, i) in [{ label: 'Campañas', ruta: '/campanas' }, ...migas]" :key="`${m.label}-${i}`">
      <ChevronRight v-if="i" :size="12" class="text-slate-300 dark:text-slate-600 shrink-0" />
      <button
        v-if="m.ruta && i < migas.length"
        type="button"
        class="font-semibold text-muted hover:text-[#2447F9] transition-colors shrink-0"
        @click="router.push(m.ruta)"
      >{{ m.label }}</button>
      <span v-else class="font-bold text-heading truncate" aria-current="page" :title="m.label">{{ m.label }}</span>
    </template>
  </nav>
</template>
