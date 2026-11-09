<script setup lang="ts">
import { computed } from 'vue'
import DatePicker from 'primevue/datepicker'
import { fieldStateClass } from '../utils/fieldStateClass'

const props = defineProps<{
  placeholder?: string
  /** Fecha mínima seleccionable, como string 'YYYY-MM-DD' (igual que el resto de la app). */
  min?: string
  /** Fecha máxima seleccionable, como string 'YYYY-MM-DD'. */
  max?: string
  disabled?: boolean
  invalid?: boolean
  valid?: boolean
  /** Altura y texto de las barras de filtros (h-9, 11px) en vez de formulario (h-10, 12px). */
  compacto?: boolean
}>()
const emit = defineEmits<{ blur: [] }>()
// String 'YYYY-MM-DD' (o '' si no hay fecha), igual que el resto de los drafts de la app.
const modelValue = defineModel<string>({ required: true })

// El DatePicker de PrimeVue trabaja con Date; el resto de la app maneja la fecha como string.
const aFecha = (v: string): Date | null => (v ? new Date(`${v}T00:00:00`) : null)
const aTexto = (d: Date): string => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const fecha = computed<Date | null>({
  get: () => aFecha(modelValue.value),
  set: (d) => { modelValue.value = d ? aTexto(d) : '' },
})

const minDate = computed(() => (props.min ? aFecha(props.min) ?? undefined : undefined))
const maxDate = computed(() => (props.max ? aFecha(props.max) ?? undefined : undefined))

// Mismo formato visual que ActivarFechaDialog.vue (el diálogo de "Activar titular/beneficiario").
const inputClass = computed(() =>
  `w-full ${props.compacto ? 'h-9 pl-3 pr-9 text-[11px]' : 'h-10 pl-4 pr-10 text-[12px]'} rounded-lg border bg-slate-50 dark:bg-slate-900 font-medium text-slate-700 dark:text-slate-100 outline-none focus:bg-white dark:focus:bg-slate-800 transition-all `
  + fieldStateClass(!!props.invalid, !!props.valid, 'border-slate-200 dark:border-slate-600 focus:border-emerald-400 focus:ring-4 focus:ring-emerald-50 dark:focus:ring-emerald-900/40'),
)
</script>

<template>
  <DatePicker
    v-model="fecha"
    :min-date="minDate"
    :max-date="maxDate"
    :disabled="disabled"
    date-format="dd/mm/yy"
    show-icon
    icon-display="input"
    fluid
    :placeholder="placeholder ?? 'Selecciona una fecha'"
    :input-class="inputClass"
    @blur="emit('blur')"
  />
</template>
