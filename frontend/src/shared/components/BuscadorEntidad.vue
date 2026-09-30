<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Search, X } from 'lucide-vue-next'

export interface OpcionBuscador {
  id: number
  label: string
  sublabel?: string
}

const props = defineProps<{
  opciones: OpcionBuscador[]
  placeholder?: string
  vacio?: string
  disabled?: boolean
  /** Nombre a mostrar para la selección actual cuando no está garantizado que
   *  venga incluida en `opciones` (ej. buscador remoto: solo trae coincidencias
   *  de la búsqueda en curso, no el catálogo completo). */
  labelSeleccionado?: string
  /** Si se pasa, el buscador consulta este callback (debounced) en vez de filtrar
   *  `opciones` localmente — para catálogos grandes que no conviene traer completos. */
  buscar?: (query: string) => Promise<OpcionBuscador[]>
}>()
const emit = defineEmits<{ blur: []; select: [item: OpcionBuscador | null] }>()

const modelValue = defineModel<number | null>({ required: true })

const abierto = ref(false)
const query = ref('')
const buscando = ref(false)
const resultadosRemotos = ref<OpcionBuscador[]>([])

const seleccionado = computed(() => {
  const enOpciones = props.opciones.find(o => o.id === modelValue.value)
  if (enOpciones) return enOpciones
  if (modelValue.value != null && props.labelSeleccionado) {
    return { id: modelValue.value, label: props.labelSeleccionado }
  }
  return null
})

let debounceTimeout: ReturnType<typeof setTimeout> | undefined
watch(query, (q) => {
  if (!props.buscar) return
  clearTimeout(debounceTimeout)
  buscando.value = true
  debounceTimeout = setTimeout(async () => {
    try {
      resultadosRemotos.value = await props.buscar!(q.trim())
    } finally {
      buscando.value = false
    }
  }, 300)
}, { immediate: true })

// Sin tildes/diacríticos en ninguno de los dos lados: un valor guardado con una
// "Ñ"/vocal acentuada en una forma Unicode distinta a la que teclea el usuario
// (visualmente idénticas, pero código a código no lo son) no debe fallar el
// match. Mismo truco que ya usa relacionamiento.api.ts (normalizarTipo) para
// el mismo problema.
const normalizar = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

const filtradas = computed(() => {
  if (props.buscar) return resultadosRemotos.value
  const q = normalizar(query.value.trim())
  if (!q) return props.opciones
  return props.opciones.filter(o => normalizar(o.label).includes(q) || (o.sublabel && normalizar(o.sublabel).includes(q)))
})

function elegir(o: OpcionBuscador) {
  modelValue.value = o.id
  query.value = ''
  abierto.value = false
  emit('select', o)
}

function limpiar() {
  modelValue.value = null
  query.value = ''
  emit('select', null)
}

function alEnfocar() {
  if (props.disabled) return
  abierto.value = true
  query.value = ''
}

function alPerderFoco() {
  setTimeout(() => { abierto.value = false; emit('blur') }, 150)
}
</script>

<template>
  <div class="relative">
    <div class="relative">
      <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" />
      <input
        :value="abierto ? query : (seleccionado?.label ?? '')"
        @input="query = ($event.target as HTMLInputElement).value; abierto = true"
        @focus="alEnfocar"
        @blur="alPerderFoco"
        :disabled="disabled"
        :placeholder="placeholder ?? 'Buscar...'"
        class="w-full h-10 pl-8 pr-8 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] text-slate-900 dark:text-slate-100 outline-none focus:bg-white dark:focus:bg-slate-800 transition-all border-slate-200 dark:border-slate-600 focus:border-[#2447F9] disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <button
        v-if="seleccionado && !disabled"
        type="button"
        @mousedown.prevent="limpiar"
        class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
      >
        <X :size="13" />
      </button>
    </div>
    <div v-if="abierto" class="absolute z-50 mt-1 w-full max-h-56 overflow-y-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-lg py-1">
      <button
        v-for="o in filtradas" :key="o.id" type="button"
        @mousedown.prevent="elegir(o)"
        class="w-full text-left px-3 py-2 text-[12px] hover:bg-[#EEF2FF] dark:hover:bg-blue-950/40 transition-colors"
      >
        <div class="font-semibold text-[#0F172A] dark:text-slate-100">{{ o.label }}</div>
        <div v-if="o.sublabel" class="text-[10px] text-slate-400 dark:text-slate-500">{{ o.sublabel }}</div>
      </button>
      <div v-if="buscando && filtradas.length === 0" class="px-3 py-2 text-[11px] text-slate-400 dark:text-slate-500">Buscando...</div>
      <div v-else-if="filtradas.length === 0" class="px-3 py-2 text-[11px] text-slate-400 dark:text-slate-500">{{ vacio ?? 'Sin resultados' }}</div>
    </div>
  </div>
</template>
