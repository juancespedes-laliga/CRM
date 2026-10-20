<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Mail, AlertTriangle } from 'lucide-vue-next'
import { authHeader } from '@/features/auth/composables/useAuth'

// Cupo diario de correos por Gmail (GET /api/correos/uso-diario). Lo comparten
// bienvenida, registro, recordatorios y "Enviar por Gmail"; el backend corta al
// llegar al tope (GMAIL_LIMITE_DIARIO) para que Google no bloquee la cuenta.
const props = defineProps<{
  /** Correos que mandaría el envío que se está preparando (avisa si no caben). */
  necesarios?: number
}>()

interface UsoDiario { fecha: string; enviados: number; limite: number | null; disponibles: number | null }

const nf = new Intl.NumberFormat('es-CO')
const uso = ref<UsoDiario | null>(null)

async function cargar() {
  try {
    const res = await fetch(`${import.meta.env.VITE_CRM_API_URL}/api/correos/uso-diario`, {
      cache: 'no-store',
      headers: authHeader(),
    })
    if (res.ok) uso.value = await res.json()
  } catch {
    // Informativo: si falla no se muestra (el backend igual aplica el tope).
  }
}
onMounted(() => void cargar())
defineExpose({ cargar })

const porcentaje = computed(() => {
  const u = uso.value
  return u?.limite ? Math.min(100, (u.enviados / u.limite) * 100) : 0
})
const noAlcanza = computed(() =>
  uso.value?.disponibles != null && (props.necesarios ?? 0) > uso.value.disponibles,
)
const colorBarra = computed(() =>
  porcentaje.value >= 90 ? 'bg-red-500' : porcentaje.value >= 70 ? 'bg-amber-500' : 'bg-[#2447F9]',
)
</script>

<template>
  <div v-if="uso?.limite" class="rounded-xl border border-default px-3 py-2 space-y-1.5">
    <div class="flex items-center justify-between gap-2 text-[11px]">
      <span class="flex items-center gap-1.5 text-muted"><Mail :size="12" /> Correos por Gmail hoy</span>
      <span class="tabular-nums text-body">
        <strong class="text-heading">{{ nf.format(uso.enviados) }}</strong> de {{ nf.format(uso.limite) }}
        · quedan <strong class="text-heading">{{ nf.format(uso.disponibles ?? 0) }}</strong>
      </span>
    </div>
    <div class="h-1.5 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
      <div class="h-full rounded-full transition-all" :class="colorBarra" :style="{ width: `${porcentaje}%` }" />
    </div>
    <p v-if="noAlcanza" class="flex items-start gap-1 text-[11px] text-red-600 dark:text-red-400">
      <AlertTriangle :size="12" class="mt-0.5 shrink-0" />
      Este envío necesita {{ nf.format(necesarios ?? 0) }} y hoy solo quedan {{ nf.format(uso.disponibles ?? 0) }}. Envíelo mañana o use MailerTurbo.
    </p>
  </div>
</template>
