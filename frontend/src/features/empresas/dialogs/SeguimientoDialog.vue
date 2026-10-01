<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, ClipboardList, CheckCircle, Loader2 } from 'lucide-vue-next'
import type { Empresa, SeguimientoEmpresaDraft } from '../types/empresa'
import { seguimientoEmpresaSchema } from '../schemas/seguimiento.schema'
import { useZodForm } from '@/shared/composables/useZodForm'
import { fieldStateClass } from '@/shared/utils/fieldStateClass'
import FieldError from '@/shared/components/FieldError.vue'
import FechaInput from '@/shared/components/FechaInput.vue'
import { TIPO_META } from '@/features/relacionamiento/constants/relacionamiento.constants'
import { createActividad } from '@/features/relacionamiento/services/relacionamiento.api'

const props = defineProps<{ empresa: Empresa | null }>()
const emit = defineEmits<{ registrado: [] }>()
const visible = defineModel<boolean>('visible', { required: true })

const segGuardado = ref(false)
const guardando = ref(false)
const error = ref<string | null>(null)
const formSeg = ref<SeguimientoEmpresaDraft>({
  tipo: 'Nota', accion: '', proximoPaso: '', proximoPasoFecha: '', fecha: new Date().toISOString().split('T')[0],
})

const { errors, tocar, esVisible, onValidSubmit } = useZodForm(seguimientoEmpresaSchema, formSeg)

watch(visible, (v) => {
  if (!v) return
  formSeg.value = { tipo: 'Nota', accion: '', proximoPaso: '', proximoPasoFecha: '', fecha: new Date().toISOString().split('T')[0] }
  segGuardado.value = false
  error.value = null
})

const guardarSeguimiento = onValidSubmit(async () => {
  if (!props.empresa) return
  guardando.value = true
  error.value = null
  try {
    await createActividad({
      tipo: formSeg.value.tipo,
      contactoId: null,
      contactoNombre: '',
      contactoDocumento: '',
      empresaNombre: props.empresa.razonSocial,
      titularId: null,
      titularNombre: '',
      titularDocumento: '',
      accion: formSeg.value.accion,
      proximoPaso: formSeg.value.proximoPaso,
      proximoPasoFecha: formSeg.value.proximoPasoFecha,
      fecha: formSeg.value.fecha,
      oportunidadId: null,
    })
    segGuardado.value = true
    emit('registrado')
    setTimeout(() => { visible.value = false; segGuardado.value = false }, 1200)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo registrar la actividad.'
  } finally {
    guardando.value = false
  }
})
</script>

<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
  >
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-[#F8FAFC] dark:bg-slate-900">
        <div>
          <h3 class="text-[14px] font-bold text-[#0F172A] dark:text-slate-100 flex items-center gap-2">
            <ClipboardList :size="15" class="text-[#2447F9]" />
            Registrar actividad
          </h3>
          <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">{{ props.empresa?.razonSocial }}</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400">
          <X :size="14" />
        </button>
      </div>

      <div v-if="segGuardado" class="p-8 text-center">
        <CheckCircle :size="36" class="text-[#2447F9] mx-auto mb-3" />
        <p class="text-[13px] font-bold text-[#0F172A] dark:text-slate-100">Actividad registrada</p>
        <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-1">Se guardó en la Bitácora de Relacionamiento</p>
      </div>

      <div v-else class="overflow-y-auto flex-1 p-6 space-y-4">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-2 uppercase tracking-wide">Tipo de actividad</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="(meta, tipo) in TIPO_META"
              :key="tipo"
              @click="formSeg.tipo = tipo as SeguimientoEmpresaDraft['tipo']"
              class="flex items-center gap-1.5 h-8 px-3 rounded-lg border text-[11px] font-semibold transition-all"
              :class="formSeg.tipo === tipo
                ? 'text-white border-transparent shadow-sm'
                : 'bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'"
              :style="formSeg.tipo === tipo ? { backgroundColor: meta.color, borderColor: meta.color } : {}"
            >
              <component :is="meta.icono" :size="12" />
              {{ tipo }}
            </button>
          </div>
        </div>

        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">¿Qué se hizo? *</label>
          <textarea
            v-model="formSeg.accion"
            @blur="tocar('accion')"
            rows="3"
            placeholder="Describe la actividad realizada..."
            class="w-full px-4 py-2.5 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] text-slate-900 dark:text-slate-100 outline-none focus:bg-white dark:focus:bg-slate-800 transition-all resize-none"
            :class="fieldStateClass(esVisible('accion') && !!errors.accion, esVisible('accion') && !errors.accion && !!formSeg.accion, 'border-slate-200 dark:border-slate-600 focus:border-[#2447F9]')"
          />
          <FieldError :message="esVisible('accion') ? errors.accion : undefined" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Próximo paso</label>
          <input
            v-model="formSeg.proximoPaso"
            placeholder="¿Qué sigue? (opcional)"
            class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] text-slate-900 dark:text-slate-100 outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all"
          />
        </div>

        <div v-if="formSeg.proximoPaso">
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Fecha límite del próximo paso</label>
          <FechaInput v-model="formSeg.proximoPasoFecha" placeholder="Opcional" />
        </div>

        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Fecha de creación</label>
          <FechaInput v-model="formSeg.fecha" disabled />
        </div>

        <p v-if="error" class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
      </div>

      <div v-if="!segGuardado" class="flex items-center justify-end gap-2 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-[#F8FAFC] dark:bg-slate-900">
        <button @click="visible = false" class="h-9 px-5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">Cancelar</button>
        <button @click="guardarSeguimiento" :disabled="guardando"
          class="flex items-center gap-1.5 h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] disabled:opacity-60 disabled:cursor-not-allowed transition-all">
          <Loader2 v-if="guardando" :size="12" class="animate-spin" />
          Guardar en Bitácora
        </button>
      </div>
    </div>
  </div>
</template>
