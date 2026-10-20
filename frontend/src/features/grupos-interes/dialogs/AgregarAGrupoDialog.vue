<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { X, Loader2, AlertCircle, CheckCircle2, UsersRound } from 'lucide-vue-next'
import type { CategoriaGrupo, GrupoInteres, PersonaParaGrupo } from '../types/grupo'
import { agregarMiembrosLote, crearCategoriasLote, getCategorias, getGrupos } from '../services/grupos.api'
import { normalizarNombre } from '../utils/normalizar'

const props = defineProps<{ personas: PersonaParaGrupo[] }>()
const visible = defineModel<boolean>('visible', { required: true })

const NUEVA = 'nueva'
const grupos = ref<GrupoInteres[]>([])
const categorias = ref<CategoriaGrupo[]>([])
const grupoId = ref<number | null>(null)
const categoria = ref<string>('') // '' = sin categoría · id · NUEVA
const nombreNueva = ref('')
const cargando = ref(false)
const guardando = ref(false)
const error = ref<string | null>(null)
const resultado = ref<{ agregados: number; yaEranMiembros: number; grupo: string; categoria: string } | null>(null)

watch(visible, async (v) => {
  if (!v) return
  resultado.value = null; error.value = null; categoria.value = ''; nombreNueva.value = ''
  cargando.value = true
  try {
    grupos.value = await getGrupos()
    grupoId.value = grupos.value[0]?.id ?? null
  } finally { cargando.value = false }
})
watch(grupoId, async (id) => {
  categoria.value = ''
  categorias.value = id === null ? [] : await getCategorias(id)
})

const grupo = computed(() => grupos.value.find((g) => g.id === grupoId.value) ?? null)
const invalido = computed(() => !grupoId.value || (categoria.value === NUEVA && !nombreNueva.value.trim()))

const confirmar = async () => {
  if (!grupoId.value || invalido.value) return
  guardando.value = true
  error.value = null
  try {
    let categoriaId: number | null = null
    let nombreCategoria = 'Sin categoría'
    if (categoria.value === NUEVA) {
      const { ids } = await crearCategoriasLote(grupoId.value, [nombreNueva.value])
      categoriaId = ids[normalizarNombre(nombreNueva.value)] ?? null
      nombreCategoria = nombreNueva.value.trim()
    } else if (categoria.value) {
      categoriaId = Number(categoria.value)
      nombreCategoria = categorias.value.find((c) => c.id === categoriaId)?.nombre ?? ''
    }
    const r = await agregarMiembrosLote(grupoId.value, props.personas.map((p, i) => ({
      filaExcel: i + 1, tipoDocumento: 'CC', documento: p.documento, nombre: p.nombre,
      correo: p.correo ?? '', telefono: p.telefono ?? '', ciudad: p.ciudad, categoria: nombreCategoria, categoriaId,
    })))
    resultado.value = { agregados: r.agregados, yaEranMiembros: r.yaEranMiembros, grupo: grupo.value?.nombre ?? '', categoria: nombreCategoria }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudieron agregar las personas al grupo.'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div>
          <h3 class="text-[14px] font-bold text-heading flex items-center gap-2"><UsersRound :size="15" /> Agregar a grupo de interés</h3>
          <p class="text-[11px] text-muted mt-0.5">{{ personas.length }} persona(s) seleccionada(s)</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-4">
        <div v-if="error" class="flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        </div>

        <div v-if="resultado" class="flex flex-col items-center text-center gap-2 py-2">
          <CheckCircle2 :size="30" class="text-emerald-500" />
          <p class="text-[13px] font-bold text-heading">Listo</p>
          <p class="text-[12px] text-body">
            <strong>{{ resultado.agregados }}</strong> persona(s) agregada(s) a «{{ resultado.grupo }}» en la categoría «{{ resultado.categoria }}».
            <template v-if="resultado.yaEranMiembros"><br>{{ resultado.yaEranMiembros }} ya eran miembros: se les actualizó la categoría.</template>
          </p>
        </div>

        <template v-else>
          <div v-if="cargando" class="flex items-center justify-center gap-2 text-[11px] text-muted py-4"><Loader2 :size="14" class="animate-spin" /> Cargando grupos...</div>
          <template v-else>
            <div>
              <label class="block text-[11px] font-semibold text-body mb-1">Grupo de interés *</label>
              <select v-model="grupoId" class="w-full h-10 px-3 rounded-lg input-surface text-[12px] outline-none cursor-pointer">
                <option v-for="g in grupos" :key="g.id" :value="g.id">{{ g.nombre }} ({{ g.totalMiembros }} miembros)</option>
              </select>
              <p v-if="!grupos.length" class="text-[10px] text-muted mt-1">No hay grupos. Créelo primero en Audiencias › Grupos de interés.</p>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-body mb-1">Categoría</label>
              <select v-model="categoria" :disabled="!grupoId" class="w-full h-10 px-3 rounded-lg input-surface text-[12px] outline-none cursor-pointer">
                <option value="">Sin categoría</option>
                <option v-for="c in categorias" :key="c.id" :value="String(c.id)">{{ c.nombre }}</option>
                <option :value="NUEVA">+ Crear categoría nueva…</option>
              </select>
              <input v-if="categoria === NUEVA" v-model="nombreNueva" placeholder="Nombre de la categoría nueva"
                class="w-full h-10 mt-2 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9]" />
            </div>
            <p class="text-[11px] text-muted">Si alguna persona ya es miembro del grupo, solo se le cambia la categoría.</p>
          </template>
        </template>
      </div>

      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-default surface-header">
        <button @click="visible = false" class="h-9 px-5 rounded-lg border-default surface-card text-[11px] font-semibold text-body surface-hover transition-all">{{ resultado ? 'Cerrar' : 'Cancelar' }}</button>
        <button v-if="!resultado" @click="confirmar" :disabled="guardando || invalido || !personas.length"
          class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50">
          <Loader2 v-if="guardando" :size="13" class="animate-spin" />
          Agregar {{ personas.length }}
        </button>
      </div>
    </div>
  </div>
</template>
