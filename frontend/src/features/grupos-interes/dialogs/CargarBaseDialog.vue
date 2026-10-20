<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  X, Upload, Download, FileSpreadsheet, Loader2, AlertCircle, AlertTriangle, CheckCircle2, Sparkles, Link2, ArrowLeft,
} from 'lucide-vue-next'
import type { CategoriaDetectada, CategoriaGrupo, FilaCargaGrupo, GrupoInteres, ResultadoCargaGrupo } from '../types/grupo'
import { descargarPlantillaGrupo, detectarCategorias, leerArchivoGrupo } from '../utils/cargaGrupo'
import { normalizarNombre } from '../utils/normalizar'
import { agregarMiembrosLote, crearCategoriasLote } from '../services/grupos.api'

const props = defineProps<{ grupo: GrupoInteres | null; categorias: CategoriaGrupo[] }>()
const emit = defineEmits<{ cargado: [] }>()
const visible = defineModel<boolean>('visible', { required: true })

type Paso = 'archivo' | 'revision' | 'resultado'
const paso = ref<Paso>('archivo')
const archivo = ref<File | null>(null)
const arrastrando = ref(false)
const leyendo = ref(false)
const procesando = ref(false)
const error = ref<string | null>(null)
const filas = ref<FilaCargaGrupo[]>([])
const detectadas = ref<CategoriaDetectada[]>([])
const resultado = ref<ResultadoCargaGrupo | null>(null)
const verErrores = ref(false)

watch(visible, (v) => {
  if (!v) return
  paso.value = 'archivo'; archivo.value = null; error.value = null
  filas.value = []; detectadas.value = []; resultado.value = null; verErrores.value = false
})

const validas = computed(() => filas.value.filter((f) => !f.error))
const conError = computed(() => filas.value.filter((f) => f.error))
const sinCategoria = computed(() => validas.value.filter((f) => !normalizarNombre(f.categoria)).length)
const nuevas = computed(() => detectadas.value.filter((d) => d.accion === 'crear'))
const existentes = computed(() => detectadas.value.filter((d) => d.existenteId !== null))

const fileInput = ref<HTMLInputElement>()
const tomarArchivo = async (f: File | undefined) => {
  if (!f || !props.grupo) return
  if (!/\.(xlsx|xls|csv)$/i.test(f.name)) { error.value = 'El archivo debe ser .xlsx, .xls o .csv.'; return }
  if (f.size > 10 * 1024 * 1024) { error.value = 'El archivo supera los 10 MB.'; return }
  archivo.value = f
  error.value = null
  leyendo.value = true
  try {
    filas.value = await leerArchivoGrupo(f)
    if (filas.value.length === 0) throw new Error('El archivo no trae filas con datos.')
    detectadas.value = detectarCategorias(filas.value, props.categorias)
    paso.value = 'revision'
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo leer el archivo.'
  } finally {
    leyendo.value = false
  }
}
const onDrop = (e: DragEvent) => { arrastrando.value = false; tomarArchivo(e.dataTransfer?.files?.[0]) }
const onInput = (e: Event) => tomarArchivo((e.target as HTMLInputElement).files?.[0])

// Dos categorías nuevas que, tras renombrarlas, terminan con el mismo nombre se crean una sola vez.
const nombresDuplicados = computed(() => {
  const vistos = new Map<string, number>()
  nuevas.value.forEach((d) => { const k = normalizarNombre(d.nombreFinal); vistos.set(k, (vistos.get(k) ?? 0) + 1) })
  return new Set([...vistos].filter(([, n]) => n > 1).map(([k]) => k))
})
const chocaConExistente = (d: CategoriaDetectada) =>
  d.accion === 'crear' && props.categorias.some((c) => normalizarNombre(c.nombre) === normalizarNombre(d.nombreFinal))
const revisionInvalida = computed(() =>
  nuevas.value.some((d) => !d.nombreFinal.trim()) || detectadas.value.some((d) => d.accion === 'unir' && d.unirConId === null))

const cambiarAccion = (d: CategoriaDetectada, valor: string) => {
  if (valor === 'crear') { d.accion = 'crear'; d.unirConId = null; return }
  d.accion = 'unir'
  d.unirConId = Number(valor)
}

const confirmar = async () => {
  if (!props.grupo) return
  procesando.value = true
  error.value = null
  try {
    // 1) Categorías nuevas (las que el usuario dejó en "crear", con su nombre final).
    const { ids, creadas } = await crearCategoriasLote(props.grupo.id, nuevas.value.map((d) => d.nombreFinal))
    const idPorClaveArchivo = new Map<string, number>()
    for (const d of detectadas.value) {
      const id = d.accion === 'crear' ? ids[normalizarNombre(d.nombreFinal)] : d.unirConId
      if (id) idPorClaveArchivo.set(d.clave, id)
    }
    // 2) Miembros, cada uno con el id de su categoría (null si venía vacía).
    const r = await agregarMiembrosLote(props.grupo.id, filas.value.map((f) => ({
      ...f, categoriaId: idPorClaveArchivo.get(normalizarNombre(f.categoria)) ?? null,
    })))
    resultado.value = { ...r, categoriasCreadas: creadas }
    paso.value = 'resultado'
    emit('cargado')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo completar la carga.'
  } finally {
    procesando.value = false
  }
}

const pasos: { key: Paso; label: string }[] = [
  { key: 'archivo', label: 'Archivo' },
  { key: 'revision', label: 'Revisar categorías' },
  { key: 'resultado', label: 'Resultado' },
]
const indicePaso = computed(() => pasos.findIndex((p) => p.key === paso.value))
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden">
      <!-- Encabezado -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div>
          <h3 class="text-[14px] font-bold text-heading flex items-center gap-2"><Upload :size="15" /> Cargar base de datos</h3>
          <p class="text-[11px] text-muted mt-0.5">
            Grupo de interés:
            <span class="font-semibold" :style="{ color: grupo?.color }">{{ grupo?.nombre }}</span>
          </p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <!-- Pasos -->
      <div class="flex items-center gap-2 px-6 pt-4">
        <template v-for="(p, i) in pasos" :key="p.key">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full text-[10px] font-bold flex items-center justify-center"
              :class="i <= indicePaso ? 'bg-[#2447F9] text-white' : 'bg-slate-100 dark:bg-slate-700 text-muted'">{{ i + 1 }}</span>
            <span class="text-[11px] font-semibold" :class="i === indicePaso ? 'text-heading' : 'text-muted'">{{ p.label }}</span>
          </div>
          <div v-if="i < pasos.length - 1" class="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
        </template>
      </div>

      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        <div v-if="error" class="flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        </div>

        <!-- PASO 1: archivo -->
        <template v-if="paso === 'archivo'">
          <div class="surface-sunken rounded-xl p-4 flex items-center justify-between gap-3">
            <div>
              <p class="text-[12px] font-semibold text-heading">Plantilla del grupo</p>
              <p class="text-[11px] text-muted mt-0.5">Una persona por fila. La columna <strong>CATEGORIA</strong> puede traer categorías que aún no existen: se crean al cargar.</p>
            </div>
            <button @click="grupo && descargarPlantillaGrupo(grupo.nombre)"
              class="flex items-center gap-1.5 h-9 px-4 rounded-lg border-default surface-card text-[11px] font-semibold text-body surface-hover transition-all shrink-0">
              <Download :size="13" /> Descargar
            </button>
          </div>

          <div @dragover.prevent="arrastrando = true" @dragleave="arrastrando = false" @drop.prevent="onDrop" @click="fileInput?.click()"
            class="border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all"
            :class="arrastrando ? 'border-[#2447F9] bg-blue-50/50 dark:bg-blue-950/20' : 'border-slate-200 dark:border-slate-700 hover:border-[#2447F9]'">
            <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" class="hidden" @change="onInput" />
            <Loader2 v-if="leyendo" :size="28" class="mx-auto text-[#2447F9] animate-spin" />
            <FileSpreadsheet v-else :size="28" class="mx-auto text-muted" />
            <p class="text-[12px] font-semibold text-heading mt-3">{{ leyendo ? 'Leyendo archivo...' : archivo?.name || 'Arrastra el archivo aquí o haz clic para seleccionarlo' }}</p>
            <p class="text-[11px] text-muted mt-1">.xlsx, .xls o .csv · máximo 10 MB</p>
          </div>
        </template>

        <!-- PASO 2: revisión de categorías -->
        <template v-if="paso === 'revision'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="surface-sunken rounded-xl p-3">
              <div class="text-[18px] font-bold text-heading tabular-nums">{{ validas.length }}</div>
              <div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Personas válidas</div>
            </div>
            <div class="surface-sunken rounded-xl p-3">
              <div class="text-[18px] font-bold tabular-nums text-slate-900 dark:text-white">{{ nuevas.length }}</div>
              <div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Categorías nuevas</div>
            </div>
            <div class="surface-sunken rounded-xl p-3">
              <div class="text-[18px] font-bold text-heading tabular-nums">{{ sinCategoria }}</div>
              <div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Sin categoría</div>
            </div>
            <div class="surface-sunken rounded-xl p-3">
              <div class="text-[18px] font-bold tabular-nums" :class="conError.length ? 'text-red-500' : 'text-heading'">{{ conError.length }}</div>
              <div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Filas con error</div>
            </div>
          </div>

          <div v-if="conError.length" class="rounded-xl border border-red-200 dark:border-red-800 bg-red-50/60 dark:bg-red-950/20 px-3 py-2">
            <button @click="verErrores = !verErrores" class="text-[11px] font-semibold text-red-600 dark:text-red-400 flex items-center gap-1.5">
              <AlertTriangle :size="12" /> {{ conError.length }} fila(s) no se van a cargar · {{ verErrores ? 'ocultar' : 'ver detalle' }}
            </button>
            <ul v-if="verErrores" class="mt-2 space-y-0.5">
              <li v-for="f in conError" :key="f.filaExcel" class="text-[11px] text-red-600 dark:text-red-400">Fila {{ f.filaExcel }}: {{ f.error }}</li>
            </ul>
          </div>

          <div>
            <h4 class="text-[12px] font-bold text-heading">Categorías encontradas en el archivo</h4>
            <p class="text-[11px] text-muted mt-0.5">Revise las nuevas antes de confirmar: puede corregir el nombre o unirlas a una categoría que ya existe.</p>
          </div>

          <p v-if="detectadas.length === 0" class="text-[12px] text-muted surface-sunken rounded-xl p-4">El archivo no trae categorías: todas las personas quedarán «Sin categoría».</p>

          <div v-else class="rounded-xl border border-default overflow-hidden">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-default surface-header">
                  <th class="px-3 py-2 text-[10px] font-bold text-muted uppercase tracking-wider">En el archivo</th>
                  <th class="px-3 py-2 text-[10px] font-bold text-muted uppercase tracking-wider text-right">Filas</th>
                  <th class="px-3 py-2 text-[10px] font-bold text-muted uppercase tracking-wider">Qué se hará</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in detectadas" :key="d.clave" class="border-b border-default last:border-0 align-top">
                  <td class="px-3 py-2.5">
                    <div class="text-[12px] font-semibold text-heading">{{ d.nombreArchivo }}</div>
                    <div v-if="d.variantes.length > 1" class="text-[10px] text-muted mt-0.5">También escrita como: {{ d.variantes.slice(1).map((v) => `«${v}»`).join(', ') }}</div>
                  </td>
                  <td class="px-3 py-2.5 text-[12px] text-body text-right tabular-nums">{{ d.filas }}</td>
                  <td class="px-3 py-2.5">
                    <div v-if="d.existenteId !== null" class="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                      <Link2 :size="12" /> Ya existe: se asigna a «{{ categorias.find((c) => c.id === d.existenteId)?.nombre }}»
                    </div>
                    <div v-else class="space-y-1.5">
                      <div class="flex flex-wrap items-center gap-2">
                        <span class="inline-flex items-center gap-1 text-[10px] font-bold text-slate-900 dark:text-white bg-[#EEF2FF] dark:bg-blue-950/40 px-2 py-0.5 rounded-md"><Sparkles :size="10" /> Nueva</span>
                        <select :value="d.accion === 'crear' ? 'crear' : String(d.unirConId)" @change="cambiarAccion(d, ($event.target as HTMLSelectElement).value)"
                          class="h-8 px-2 rounded-lg input-surface text-[11px] font-medium text-body outline-none cursor-pointer">
                          <option value="crear">Crear como categoría nueva</option>
                          <optgroup v-if="categorias.length" label="Unir con una existente">
                            <option v-for="c in categorias" :key="c.id" :value="String(c.id)">{{ c.nombre }}</option>
                          </optgroup>
                        </select>
                      </div>
                      <div v-if="d.accion === 'crear'">
                        <input v-model="d.nombreFinal" placeholder="Nombre de la categoría"
                          class="w-full max-w-xs h-8 px-2.5 rounded-lg input-surface text-[11px] outline-none focus:border-[#2447F9]" />
                        <p v-if="!d.nombreFinal.trim()" class="text-[10px] text-red-500 mt-0.5">Escriba un nombre.</p>
                        <p v-else-if="chocaConExistente(d)" class="text-[10px] text-amber-600 dark:text-amber-400 mt-0.5">Ese nombre ya existe en el grupo: se usará la categoría existente.</p>
                        <p v-else-if="nombresDuplicados.has(normalizarNombre(d.nombreFinal))" class="text-[10px] text-amber-600 dark:text-amber-400 mt-0.5">Otra categoría nueva tiene el mismo nombre: se crearán como una sola.</p>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="existentes.length" class="text-[10px] text-muted">{{ existentes.length }} categoría(s) del archivo ya existían en el grupo (se compara sin tildes ni mayúsculas).</p>
        </template>

        <!-- PASO 3: resultado -->
        <template v-if="paso === 'resultado' && resultado">
          <div class="flex flex-col items-center text-center gap-2 py-2">
            <CheckCircle2 :size="34" class="text-emerald-500" />
            <h4 class="text-[14px] font-bold text-heading">Carga completada</h4>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="surface-sunken rounded-xl p-3"><div class="text-[18px] font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">{{ resultado.agregados }}</div><div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Agregados al grupo</div></div>
            <div class="surface-sunken rounded-xl p-3"><div class="text-[18px] font-bold text-heading tabular-nums">{{ resultado.yaEranMiembros }}</div><div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Ya eran miembros</div></div>
            <div class="surface-sunken rounded-xl p-3"><div class="text-[18px] font-bold text-heading tabular-nums">{{ resultado.contactosNuevos }}</div><div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Contactos nuevos en el CRM</div></div>
            <div class="surface-sunken rounded-xl p-3"><div class="text-[18px] font-bold tabular-nums" :class="resultado.errores.length ? 'text-red-500' : 'text-heading'">{{ resultado.errores.length }}</div><div class="text-[10px] text-muted uppercase font-semibold tracking-wide">Filas con error</div></div>
          </div>
          <div v-if="resultado.categoriasCreadas.length" class="surface-sunken rounded-xl p-3">
            <p class="text-[11px] font-semibold text-heading mb-1.5">Categorías creadas ({{ resultado.categoriasCreadas.length }})</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="c in resultado.categoriasCreadas" :key="c" class="text-[11px] font-semibold px-2.5 py-1 rounded-md text-white" :style="{ backgroundColor: grupo?.color }">{{ c }}</span>
            </div>
          </div>
          <p class="text-[11px] text-muted">Quienes ya eran miembros del grupo quedaron con la categoría que traía el archivo.</p>
        </template>
      </div>

      <!-- Pie -->
      <div class="flex items-center justify-between gap-2 px-6 py-4 border-t border-default surface-header">
        <button v-if="paso === 'revision'" @click="paso = 'archivo'" :disabled="procesando"
          class="flex items-center gap-1 h-9 px-4 rounded-lg text-[11px] font-semibold text-body surface-hover transition-all"><ArrowLeft :size="13" /> Cambiar archivo</button>
        <span v-else />
        <div class="flex items-center gap-2">
          <button @click="visible = false" class="h-9 px-5 rounded-lg border-default surface-card text-[11px] font-semibold text-body surface-hover transition-all">
            {{ paso === 'resultado' ? 'Cerrar' : 'Cancelar' }}
          </button>
          <button v-if="paso === 'revision'" @click="confirmar" :disabled="procesando || revisionInvalida || validas.length === 0"
            class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-50">
            <Loader2 v-if="procesando" :size="13" class="animate-spin" />
            {{ procesando ? 'Cargando...' : `Cargar ${validas.length} persona(s)` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
