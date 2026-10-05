<script setup lang="ts">
import { ref } from 'vue'
import { X, AlertCircle, Check } from 'lucide-vue-next'
import type { GrupoDraft } from '../types/grupo'
import { COLORES_GRUPO } from '../constants/grupos.constants'

defineProps<{ modo: 'nuevo' | 'editar'; error?: string | null; guardando?: boolean }>()
const emit = defineEmits<{ submit: [] }>()

const visible = defineModel<boolean>('visible', { required: true })
const draft = defineModel<GrupoDraft>('draft', { required: true })

const intento = ref(false)
const enviar = () => {
  intento.value = true
  if (!draft.value.nombre.trim()) return
  emit('submit')
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-[99999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md flex flex-col overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b border-default surface-header">
        <div>
          <h3 class="text-[14px] font-bold text-heading">{{ modo === 'nuevo' ? 'Nuevo grupo de interés' : 'Editar grupo de interés' }}</h3>
          <p class="text-[11px] text-muted mt-0.5">Las categorías se agregan después, o se crean solas al cargar la base</p>
        </div>
        <button @click="visible = false" class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 flex items-center justify-center text-slate-500 dark:text-slate-400"><X :size="14" /></button>
      </div>

      <div class="p-6 space-y-4">
        <div v-if="error" class="flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl px-3 py-2">
          <AlertCircle :size="13" class="text-red-500 dark:text-red-400 shrink-0" />
          <p class="text-[11px] text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        </div>

        <div>
          <label class="block text-[11px] font-semibold text-body mb-1">Nombre *</label>
          <input v-model="draft.nombre" placeholder="Ej: Donantes, Voluntarios, Aliados..." @keydown.enter="enviar"
            class="w-full h-10 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] transition-all" />
          <p v-if="intento && !draft.nombre.trim()" class="text-[10px] text-red-500 mt-1">Escriba el nombre del grupo.</p>
        </div>

        <div>
          <label class="block text-[11px] font-semibold text-body mb-1">Descripción</label>
          <textarea v-model="draft.descripcion" rows="2" placeholder="¿Quiénes hacen parte de este grupo?"
            class="w-full px-3 py-2 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] transition-all resize-none" />
        </div>

        <div>
          <label class="block text-[11px] font-semibold text-body mb-1.5">Color</label>
          <div class="flex flex-wrap gap-2">
            <button v-for="c in COLORES_GRUPO" :key="c" type="button" @click="draft.color = c" :title="c"
              class="w-8 h-8 rounded-lg flex items-center justify-center transition-transform hover:scale-105"
              :style="{ backgroundColor: c }">
              <Check v-if="draft.color === c" :size="14" class="text-white" />
            </button>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 px-6 py-4 border-t border-default surface-header">
        <button @click="visible = false" class="h-9 px-5 rounded-lg border-default surface-card text-[11px] font-semibold text-body surface-hover transition-all">Cancelar</button>
        <button @click="enviar" :disabled="guardando" class="h-9 px-6 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all disabled:opacity-60">
          {{ guardando ? 'Guardando...' : modo === 'nuevo' ? 'Crear grupo' : 'Guardar cambios' }}
        </button>
      </div>
    </div>
  </div>
</template>
