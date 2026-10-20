<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { X, AlertCircle, UserPlus, Loader2 } from 'lucide-vue-next'
import type { CategoriaGrupo, GrupoInteres, MiembroGrupo } from '../types/grupo'
import { agregarMiembrosLote, crearCategoriasLote } from '../services/grupos.api'
import { normalizarNombre } from '../utils/normalizar'
import { joinNombreCompleto } from '@/shared/utils/nombreCompuesto'

const props = defineProps<{ grupo: GrupoInteres | null; categorias: CategoriaGrupo[]; miembros: MiembroGrupo[] }>()
const emit = defineEmits<{ agregado: [] }>()
const visible = defineModel<boolean>('visible', { required: true })

const TIPOS_DOC = ['CC', 'TI', 'CE', 'PA', 'RC', 'NIT']
const NUEVA = 'nueva'

const vacio = () => ({
  tipoDocumento: 'CC', documento: '', nombre1: '', nombre2: '', apellido1: '', apellido2: '',
  correo: '', telefono: '', ciudad: '', categoria: '', nombreCategoriaNueva: '',
})
const form = reactive(vacio())
const intento = ref(false)
const guardando = ref(false)
const error = ref<string | null>(null)
const agregarOtra = ref(false)

watch(visible, (v) => {
  if (!v) return
  Object.assign(form, vacio())
  intento.value = false
  error.value = null
})

const documentoLimpio = computed(() => form.documento.replace(/[^\dA-Za-z]/g, ''))
const yaEsMiembro = computed(() => props.miembros.find((m) => m.documento === documentoLimpio.value) ?? null)
const correoInvalido = computed(() => !!form.correo.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.correo.trim()))
const errores = computed(() => ({
  documento: !documentoLimpio.value ? 'Escriba el número de documento.' : yaEsMiembro.value ? `Ya es miembro del grupo (${yaEsMiembro.value.nombre}).` : '',
  nombre1: !form.nombre1.trim() ? 'Escriba el primer nombre.' : '',
  apellido1: !form.apellido1.trim() ? 'Escriba el primer apellido.' : '',
  correo: correoInvalido.value ? 'El correo no tiene un formato válido.' : '',
  categoria: form.categoria === NUEVA && !form.nombreCategoriaNueva.trim() ? 'Escriba el nombre de la categoría nueva.' : '',
}))
const hayErrores = computed(() => Object.values(errores.value).some(Boolean))
const err = (campo: keyof typeof errores.value) => (intento.value ? errores.value[campo] : '')

const guardar = async (seguir: boolean) => {
  intento.value = true
  if (hayErrores.value || !props.grupo) return
  guardando.value = true
  error.value = null
  try {
    let categoriaId: number | null = null
    let nombreCategoria = ''
    if (form.categoria === NUEVA) {
      const { ids } = await crearCategoriasLote(props.grupo.id, [form.nombreCategoriaNueva])
      categoriaId = ids[normalizarNombre(form.nombreCategoriaNueva)] ?? null
      nombreCategoria = form.nombreCategoriaNueva
    } else if (form.categoria) {
      categoriaId = Number(form.categoria)
      nombreCategoria = props.categorias.find((c) => c.id === categoriaId)?.nombre ?? ''
    }
    await agregarMiembrosLote(props.grupo.id, [{
      filaExcel: 1, tipoDocumento: form.tipoDocumento, documento: documentoLimpio.value,
      nombre: joinNombreCompleto({ nombre1: form.nombre1, nombre2: form.nombre2, apellido1: form.apellido1, apellido2: form.apellido2 }),
      correo: form.correo.trim(), telefono: form.telefono.trim(), ciudad: form.ciudad.trim(), categoria: nombreCategoria, categoriaId,
    }])
    emit('agregado')
    if (seguir) {
      // Conserva tipo de documento y categoría para cargar varias seguidas del mismo tipo.
      const { tipoDocumento, categoria } = form
      Object.assign(form, vacio(), { tipoDocumento, categoria: categoria === NUEVA ? String(categoriaId ?? '') : categoria })
      intento.value = false
      agregarOtra.value = true
      setTimeout(() => { agregarOtra.value = false }, 2500)
    } else {
      visible.value = false
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo agregar la persona.'
  } finally {
    guardando.value = false
  }
}

const INPUT = 'w-full h-9 px-3 rounded-md border bg-white dark:bg-slate-900 text-[12px] text-heading outline-none transition-colors focus:border-[#2447F9] focus:ring-2 focus:ring-[#2447F9]/15'
const borde = (e: string) => (e ? 'border-red-400 dark:border-red-500' : 'border-slate-200 dark:border-slate-600')
const LABEL = 'block text-[11px] font-semibold text-body mb-1'
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-slate-900/40 backdrop-blur-[2px] p-4">
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-xl flex flex-col overflow-hidden max-h-[92vh]">
      <div class="flex items-start justify-between px-6 py-4 border-b border-default">
        <div>
          <h3 class="text-[14px] font-bold text-heading flex items-center gap-2"><UserPlus :size="15" class="text-[#2447F9]" /> Agregar persona</h3>
          <p class="text-[11px] text-muted mt-0.5">
            Al grupo <span class="font-semibold" :style="{ color: grupo?.color }">{{ grupo?.nombre }}</span>.
            Para muchas personas a la vez, use «Cargar Excel».
          </p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-md text-muted hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center justify-center" title="Cerrar"><X :size="15" /></button>
      </div>

      <div class="p-6 space-y-5 overflow-y-auto">
        <div v-if="error" class="flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-md px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        </div>
        <div v-if="agregarOtra" class="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-md px-3 py-2 text-[11px] font-medium text-emerald-700 dark:text-emerald-300">
          Persona agregada. Puede seguir con la siguiente.
        </div>

        <!-- Identificación -->
        <fieldset class="space-y-3">
          <legend class="text-[10px] font-bold text-subtle uppercase tracking-wider mb-2">Identificación</legend>
          <div class="grid grid-cols-[110px_minmax(0,1fr)] gap-3">
            <div>
              <label :class="LABEL" for="ap-tipo">Tipo</label>
              <select id="ap-tipo" v-model="form.tipoDocumento" :class="[INPUT, borde('')]" class="cursor-pointer">
                <option v-for="t in TIPOS_DOC" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div>
              <label :class="LABEL" for="ap-doc">Documento *</label>
              <input id="ap-doc" v-model="form.documento" placeholder="Número de documento" :class="[INPUT, borde(err('documento'))]" />
              <p v-if="err('documento')" class="text-[10px] text-red-500 mt-1">{{ err('documento') }}</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label :class="LABEL" for="ap-n1">Primer nombre *</label>
              <input id="ap-n1" v-model="form.nombre1" :class="[INPUT, borde(err('nombre1'))]" />
              <p v-if="err('nombre1')" class="text-[10px] text-red-500 mt-1">{{ err('nombre1') }}</p>
            </div>
            <div>
              <label :class="LABEL" for="ap-n2">Segundo nombre</label>
              <input id="ap-n2" v-model="form.nombre2" :class="[INPUT, borde('')]" />
            </div>
            <div>
              <label :class="LABEL" for="ap-a1">Primer apellido *</label>
              <input id="ap-a1" v-model="form.apellido1" :class="[INPUT, borde(err('apellido1'))]" />
              <p v-if="err('apellido1')" class="text-[10px] text-red-500 mt-1">{{ err('apellido1') }}</p>
            </div>
            <div>
              <label :class="LABEL" for="ap-a2">Segundo apellido</label>
              <input id="ap-a2" v-model="form.apellido2" :class="[INPUT, borde('')]" />
            </div>
          </div>
        </fieldset>

        <!-- Contacto -->
        <fieldset class="space-y-3">
          <legend class="text-[10px] font-bold text-subtle uppercase tracking-wider mb-2">Contacto</legend>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label :class="LABEL" for="ap-correo">Correo</label>
              <input id="ap-correo" v-model="form.correo" type="email" placeholder="nombre@dominio.com" :class="[INPUT, borde(err('correo'))]" />
              <p v-if="err('correo')" class="text-[10px] text-red-500 mt-1">{{ err('correo') }}</p>
            </div>
            <div>
              <label :class="LABEL" for="ap-tel">Teléfono</label>
              <input id="ap-tel" v-model="form.telefono" placeholder="300 000 0000" :class="[INPUT, borde('')]" />
            </div>
            <div class="col-span-2">
              <label :class="LABEL" for="ap-ciudad">Ciudad</label>
              <input id="ap-ciudad" v-model="form.ciudad" placeholder="Ej: Pereira" :class="[INPUT, borde('')]" />
            </div>
          </div>
        </fieldset>

        <!-- Clasificación -->
        <fieldset class="space-y-3">
          <legend class="text-[10px] font-bold text-subtle uppercase tracking-wider mb-2">Clasificación en el grupo</legend>
          <div>
            <label :class="LABEL" for="ap-cat">Categoría</label>
            <select id="ap-cat" v-model="form.categoria" :class="[INPUT, borde('')]" class="cursor-pointer">
              <option value="">Sin categoría</option>
              <option v-for="c in categorias" :key="c.id" :value="String(c.id)">{{ c.nombre }}</option>
              <option :value="NUEVA">+ Crear categoría nueva…</option>
            </select>
            <input v-if="form.categoria === NUEVA" v-model="form.nombreCategoriaNueva" placeholder="Nombre de la categoría nueva"
              :class="[INPUT, borde(err('categoria'))]" class="mt-2" />
            <p v-if="err('categoria')" class="text-[10px] text-red-500 mt-1">{{ err('categoria') }}</p>
          </div>
        </fieldset>
      </div>

      <div class="flex items-center justify-between gap-2 px-6 py-4 border-t border-default bg-slate-50/60 dark:bg-slate-900/30">
        <button @click="visible = false" class="h-9 px-4 rounded-md text-[12px] font-semibold text-body hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">Cancelar</button>
        <div class="flex items-center gap-2">
          <button @click="guardar(true)" :disabled="guardando"
            class="h-9 px-4 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[12px] font-semibold text-body hover:border-slate-400 transition-colors disabled:opacity-50">
            Guardar y agregar otra
          </button>
          <button @click="guardar(false)" :disabled="guardando"
            class="flex items-center gap-1.5 h-9 px-5 rounded-md bg-[#2447F9] text-white text-[12px] font-semibold hover:bg-[#1D3DD9] transition-colors disabled:opacity-50">
            <Loader2 v-if="guardando" :size="13" class="animate-spin" /> Agregar al grupo
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
