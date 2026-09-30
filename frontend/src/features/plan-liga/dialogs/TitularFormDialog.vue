<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, AlertCircle } from 'lucide-vue-next'
import type { PlanServicio, TitularDraft } from '../types/plan-liga'
import TitularForm from '../forms/TitularForm.vue'

defineProps<{
  modo: 'nuevo' | 'editar'
  guardando?: boolean
  error?: string | null
  planesServicio?: PlanServicio[]
}>()
const emit = defineEmits<{ submit: [enviarCorreo: boolean] }>()

const visible = defineModel<boolean>('visible', { required: true })
const draft = defineModel<TitularDraft>('draft', { required: true })

const formRef = ref<InstanceType<typeof TitularForm>>()
// Solo aplica al crear (modo 'nuevo'); desmarcado por defecto cada vez que se
// abre el modal -- el correo solo se manda si se elige a propósito.
const enviarCorreo = ref(false)
watch(visible, (v) => { if (v) enviarCorreo.value = false })
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-[#F8FAFC] dark:bg-slate-900">
        <div>
          <h3 class="text-[14px] font-bold text-[#0F172A] dark:text-slate-100">{{ modo === 'nuevo' ? 'Nuevo Titular' : 'Editar Titular' }}</h3>
          <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Programa Plan Liga Ama Salvar Vidas</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>
      <div class="overflow-y-auto flex-1 p-6">
        <div v-if="error" class="mb-4 flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        </div>
        <TitularForm ref="formRef" v-model="draft" :modo="modo" :planes-servicio="planesServicio" @valid-submit="emit('submit', enviarCorreo)" />
        <label v-if="modo === 'nuevo'" class="flex items-center gap-2 mt-4 cursor-pointer select-none">
          <input type="checkbox" v-model="enviarCorreo" class="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-[#EC4899] focus:ring-[#EC4899]" />
          <span class="text-[11px] text-slate-600 dark:text-slate-300">Enviar correo de registro a este titular</span>
        </label>
      </div>
      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-[#F8FAFC] dark:bg-slate-900">
        <button @click="visible = false" class="h-9 px-5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">Cancelar</button>
        <button @click="formRef?.submit()" :disabled="guardando"
          class="h-9 px-6 rounded-lg bg-[#EC4899] text-white text-[11px] font-bold shadow hover:bg-[#D61F69] transition-all disabled:opacity-60 disabled:cursor-not-allowed">
          {{ guardando
            ? (modo === 'nuevo' && enviarCorreo ? 'Enviando notificación por correo...' : 'Guardando...')
            : (modo === 'nuevo' ? 'Crear titular' : 'Guardar cambios') }}
        </button>
      </div>
    </div>
  </div>
</template>
