<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { Plus, Pencil, Trash2, Check, X, Tags } from 'lucide-vue-next'
import type { CategoriaGrupo } from '../types/grupo'
import type { FiltroCategoria } from '../composables/useGruposInteres'

const props = defineProps<{
  categorias: CategoriaGrupo[]
  totalMiembros: number
  sinCategoria: number
  color: string
  puedeGestionar: boolean
}>()
const emit = defineEmits<{
  crear: [nombre: string]
  renombrar: [id: number, nombre: string]
  eliminar: [categoria: CategoriaGrupo]
}>()
const filtro = defineModel<FiltroCategoria>('filtro', { required: true })

const creando = ref(false)
const nombreNueva = ref('')
const inputNueva = ref<HTMLInputElement>()
const abrirNueva = async () => {
  creando.value = true
  nombreNueva.value = ''
  await nextTick()
  inputNueva.value?.focus()
}
const confirmarNueva = () => {
  if (!nombreNueva.value.trim()) { creando.value = false; return }
  emit('crear', nombreNueva.value)
  creando.value = false
}

const editandoId = ref<number | null>(null)
const nombreEdicion = ref('')
const editar = (c: CategoriaGrupo) => { editandoId.value = c.id; nombreEdicion.value = c.nombre }
const confirmarEdicion = () => {
  if (editandoId.value !== null && nombreEdicion.value.trim()) emit('renombrar', editandoId.value, nombreEdicion.value)
  editandoId.value = null
}

const pct = (n: number) => (props.totalMiembros ? Math.round((n / props.totalMiembros) * 100) : 0)
// Tarjeta seleccionada: borde del color del grupo; el resto, borde neutro.
const estiloTarjeta = (activa: boolean) => (activa ? { borderColor: props.color, boxShadow: `inset 0 0 0 1px ${props.color}` } : {})
</script>

<template>
  <div class="surface-card rounded-lg border border-default shadow-sm px-4 py-3">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-[12px] font-bold text-heading flex items-center gap-1.5"><Tags :size="14" class="text-muted" /> Categorías</h3>
      <div class="flex items-center gap-3">
        <span class="hidden md:inline text-[11px] text-muted">Clic en una tarjeta para ver solo esos miembros</span>
        <button v-if="puedeGestionar && !creando" type="button" @click="abrirNueva"
          class="h-7 px-2.5 rounded-md border border-slate-200 dark:border-slate-600 text-[11px] font-semibold text-body hover:border-slate-400 transition-colors flex items-center gap-1">
          <Plus :size="12" /> Nueva categoría
        </button>
      </div>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-2.5">
      <!-- Todas -->
      <button type="button" @click="filtro = 'todas'" :style="estiloTarjeta(filtro === 'todas')"
        class="text-left rounded-lg border border-default bg-white dark:bg-slate-800 px-3 py-2.5 hover:border-slate-400 transition-colors">
        <div class="text-[10px] font-bold text-subtle uppercase tracking-wide">Todas</div>
        <div class="text-[20px] font-bold text-heading tabular-nums leading-tight mt-0.5">{{ totalMiembros }}</div>
        <div class="text-[10px] text-muted">miembros del grupo</div>
      </button>

      <!-- Una tarjeta por categoría -->
      <div v-for="c in categorias" :key="c.id" class="group relative">
        <div v-if="editandoId === c.id" class="h-full rounded-lg border border-[#2447F9] bg-white dark:bg-slate-800 px-3 py-2.5 flex flex-col gap-2">
          <input v-model="nombreEdicion" @keydown.enter="confirmarEdicion" @keydown.esc="editandoId = null"
            class="w-full h-7 px-2 rounded-md input-surface text-[11px] font-semibold text-heading outline-none" />
          <div class="flex gap-1">
            <button @click="confirmarEdicion" class="flex-1 h-7 rounded-md bg-[#2447F9] text-white text-[10px] font-bold flex items-center justify-center gap-1"><Check :size="11" /> Guardar</button>
            <button @click="editandoId = null" class="h-7 w-7 rounded-md border border-default text-muted flex items-center justify-center" title="Cancelar"><X :size="11" /></button>
          </div>
        </div>
        <button v-else type="button" @click="filtro = c.id" :style="estiloTarjeta(filtro === c.id)"
          class="w-full h-full text-left rounded-lg border border-default bg-white dark:bg-slate-800 px-3 py-2.5 hover:border-slate-400 transition-colors">
          <div class="text-[10px] font-bold text-subtle uppercase tracking-wide truncate pr-12" :title="c.nombre">{{ c.nombre }}</div>
          <div class="flex items-baseline gap-1.5 mt-0.5">
            <span class="text-[20px] font-bold text-heading tabular-nums leading-tight">{{ c.totalMiembros }}</span>
            <span class="text-[10px] text-muted tabular-nums">{{ pct(c.totalMiembros) }}%</span>
          </div>
          <div class="mt-1.5 h-1 rounded-sm bg-slate-100 dark:bg-slate-700 overflow-hidden">
            <div class="h-full rounded-sm" :style="{ width: pct(c.totalMiembros) + '%', backgroundColor: color }" />
          </div>
        </button>
        <div v-if="puedeGestionar && editandoId !== c.id" class="absolute top-1.5 right-1.5 hidden group-hover:flex items-center gap-0.5">
          <button @click.stop="editar(c)" class="w-6 h-6 rounded-md flex items-center justify-center text-muted hover:text-[#2447F9] hover:bg-slate-100 dark:hover:bg-slate-700" title="Renombrar"><Pencil :size="11" /></button>
          <button @click.stop="emit('eliminar', c)" class="w-6 h-6 rounded-md flex items-center justify-center text-muted hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40" title="Eliminar"><Trash2 :size="11" /></button>
        </div>
      </div>

      <!-- Sin categoría -->
      <button type="button" @click="filtro = 'sin'" :style="estiloTarjeta(filtro === 'sin')"
        class="text-left rounded-lg border border-dashed border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2.5 hover:border-slate-400 transition-colors">
        <div class="text-[10px] font-bold text-subtle uppercase tracking-wide">Sin categoría</div>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <span class="text-[20px] font-bold text-heading tabular-nums leading-tight">{{ sinCategoria }}</span>
          <span class="text-[10px] text-muted tabular-nums">{{ pct(sinCategoria) }}%</span>
        </div>
        <div class="text-[10px] text-muted">por clasificar</div>
      </button>

      <!-- Nueva categoría (formulario en línea; se abre desde el botón del encabezado) -->
      <template v-if="puedeGestionar">
        <div v-if="creando" class="rounded-lg border border-[#2447F9] bg-white dark:bg-slate-800 px-3 py-2.5 flex flex-col gap-2">
          <input ref="inputNueva" v-model="nombreNueva" placeholder="Nombre de la categoría"
            @keydown.enter="confirmarNueva" @keydown.esc="creando = false"
            class="w-full h-7 px-2 rounded-md input-surface text-[11px] font-semibold text-heading outline-none" />
          <div class="flex gap-1">
            <button @click="confirmarNueva" class="flex-1 h-7 rounded-md bg-[#2447F9] text-white text-[10px] font-bold flex items-center justify-center gap-1"><Check :size="11" /> Crear</button>
            <button @click="creando = false" class="h-7 w-7 rounded-md border border-default text-muted flex items-center justify-center" title="Cancelar"><X :size="11" /></button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
