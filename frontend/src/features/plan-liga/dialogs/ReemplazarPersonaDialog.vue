<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, AlertTriangle, AlertCircle, RefreshCw, UserCheck } from 'lucide-vue-next'
import type { Beneficiario, ReemplazoPersonaDraft } from '../types/plan-liga'
import ReemplazoPersonaForm from '../forms/ReemplazoPersonaForm.vue'

const props = defineProps<{
  tipo: 'titular' | 'beneficiario'
  nombreActual?: string
  documentoActual?: string
  /** Solo aplica a beneficiario: para dar contexto de a qué titular pertenece. */
  titularNombre?: string
  /** Solo aplica a titular: beneficiarios del grupo (activos e inactivos). Si el documento
   *  escrito coincide con uno, se llenan sus datos y el backend lo promueve a titular. */
  beneficiariosGrupo?: Beneficiario[]
  guardando?: boolean
  error?: string | null
}>()
const emit = defineEmits<{ submit: [] }>()

const visible = defineModel<boolean>('visible', { required: true })
const draft = defineModel<ReemplazoPersonaDraft>('draft', { required: true })

const confirmado = ref(false)
// Cada vez que se abre el diálogo para un caso nuevo, exige reconfirmar: no se hereda
// el "entiendo las consecuencias" de un reemplazo anterior.
watch(visible, (v) => { if (v) { confirmado.value = false; beneficiarioEncontrado.value = null } })

const beneficiarioEncontrado = ref<Beneficiario | null>(null)
const alSalirDocumento = (documento: string) => {
  if (props.tipo !== 'titular' || !props.beneficiariosGrupo) return
  const doc = documento.trim()
  const b = doc ? props.beneficiariosGrupo.find(x => x.documento.trim() === doc) : undefined
  beneficiarioEncontrado.value = b ?? null
  if (!b) return
  draft.value = {
    tipoDocumento: b.tipoDocumento || draft.value.tipoDocumento,
    documento: b.documento,
    nombre: b.nombre,
    fechaNacimiento: b.fechaNacimiento,
    sexo: b.sexo,
    correo: b.correo,
    telefono: b.telefono,
    direccion: b.direccion,
    ciudad: b.ciudad,
    departamento: b.departamento,
    empresa: b.empresa,
  }
}

const formRef = ref<InstanceType<typeof ReemplazoPersonaForm>>()

const cerrar = () => { visible.value = false }
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[999999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-amber-50 dark:bg-amber-950/30 shrink-0">
        <div>
          <h3 class="text-[14px] font-bold text-[#0F172A] dark:text-slate-100 flex items-center gap-2">
            <RefreshCw :size="15" class="text-amber-600 dark:text-amber-400" />
            Reemplazar {{ props.tipo === 'titular' ? 'titular' : 'beneficiario' }}
          </h3>
          <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
            {{ props.nombreActual }}<template v-if="props.documentoActual"> · {{ props.documentoActual }}</template>
            <template v-if="props.tipo === 'beneficiario' && props.titularNombre"> · Titular: {{ props.titularNombre }}</template>
          </p>
        </div>
        <button @click="cerrar" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="overflow-y-auto flex-1 p-6">
        <div class="mb-5 flex items-start gap-2.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl px-3.5 py-3">
          <AlertTriangle :size="15" class="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <p class="text-[11px] text-amber-800 dark:text-amber-300 leading-relaxed">
            Esto <strong>no es una edición</strong>. Da de baja a <strong>{{ props.nombreActual }}</strong> y da de alta a una
            persona nueva en su lugar, heredando plan, cupo y orden{{ props.tipo === 'titular' ? ' del titular anterior' : '' }}.
            Incluye las altas/bajas correspondientes en Servinte (ABPAC/INCLE). Esta acción no se puede deshacer.
          </p>
        </div>

        <div v-if="props.error" class="mb-4 flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ props.error }}</p>
        </div>

        <p v-if="props.tipo === 'titular' && props.beneficiariosGrupo?.length && !beneficiarioEncontrado" class="mb-4 text-[11px] text-slate-500 dark:text-slate-400">
          Si el nuevo titular es un beneficiario de este grupo, escribe solo su <strong>documento</strong> y sus datos se llenan solos.
        </p>

        <div v-if="beneficiarioEncontrado" class="mb-4 flex items-start gap-2.5 bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800 rounded-xl px-3.5 py-3">
          <UserCheck :size="15" class="text-sky-600 dark:text-sky-400 shrink-0 mt-0.5" />
          <p class="text-[11px] text-sky-800 dark:text-sky-300 leading-relaxed">
            <strong>{{ beneficiarioEncontrado.nombre }}</strong> es beneficiario(a) de este grupo. Al confirmar, quedará como
            titular y su registro de beneficiario se inactivará (queda como historial en el grupo anterior).
          </p>
        </div>

        <ReemplazoPersonaForm ref="formRef" v-model="draft" @valid-submit="emit('submit')" @documento-blur="alSalirDocumento" />

        <label class="mt-6 flex items-start gap-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-3.5 py-3 cursor-pointer">
          <input v-model="confirmado" type="checkbox" class="mt-0.5 w-4 h-4 accent-amber-600 cursor-pointer" />
          <span class="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed">
            Entiendo que esto da de baja a <strong>{{ props.nombreActual }}</strong> y da de alta a la persona nueva en su lugar,
            incluyendo Servinte (ABPAC/INCLE), y que no se puede deshacer.
          </span>
        </label>
      </div>

      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-[#F8FAFC] dark:bg-slate-900 shrink-0">
        <button @click="cerrar" class="h-9 px-5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">Cancelar</button>
        <button @click="formRef?.submit()" :disabled="props.guardando || !confirmado"
          class="h-9 px-6 rounded-lg bg-amber-600 text-white text-[11px] font-bold shadow hover:bg-amber-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
          {{ props.guardando ? 'Reemplazando...' : 'Confirmar reemplazo' }}
        </button>
      </div>
    </div>
  </div>
</template>
