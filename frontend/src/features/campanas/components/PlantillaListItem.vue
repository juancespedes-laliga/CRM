<script setup lang="ts">
import { FileCode2, Pencil, Send, Megaphone, Copy, Download, Trash2 } from 'lucide-vue-next'
import type { Plantilla } from '../types/plantilla'
import { fmtFechaPlantilla, descargarHtml } from '../constants/campanas.constants'
import { permisosDeModulo, tienePermiso } from '@/features/auth/composables/useAuth'

const props = defineProps<{ plantilla: Plantilla }>()
const emit = defineEmits<{ editar: []; enviar: []; enviarMailer: []; duplicar: []; eliminar: [] }>()

const { gestionar: puedeGestionar } = permisosDeModulo('campanas')
const puedeEnviarMailer = tienePermiso('mailerturbo:enviar')

const descargar = () => descargarHtml(props.plantilla.nombre, props.plantilla.html)
</script>

<template>
  <div class="flex items-center gap-4 px-5 py-4 hover:bg-slate-50/60 dark:hover:bg-slate-700/60 transition-colors group">
    <div class="w-10 h-10 rounded-xl bg-[#F3E8FF] dark:bg-purple-950/40 flex items-center justify-center flex-shrink-0">
      <FileCode2 :size="17" class="text-[#7C3AED] dark:text-purple-300" />
    </div>

    <button class="flex-1 min-w-0 text-left" @click="emit('editar')">
      <div class="text-[12px] font-bold text-heading truncate">{{ plantilla.nombre }}</div>
      <div class="flex items-center gap-2 text-[10px] text-muted mt-0.5">
        <span class="truncate">{{ plantilla.asunto || 'Sin asunto' }}</span>
        <span class="shrink-0">· editada {{ fmtFechaPlantilla(plantilla.actualizadoEn) }}</span>
      </div>
    </button>

    <div v-if="puedeGestionar" class="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-all">
      <button @click="emit('editar')" title="Editar" class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-[#2447F9] hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"><Pencil :size="13" /></button>
      <button v-if="puedeEnviarMailer" @click="emit('enviarMailer')" title="Enviar como campaña (MailerTurbo)" class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-[#2447F9] hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"><Megaphone :size="13" /></button>
      <button @click="emit('enviar')" title="Enviar por Gmail (pocos destinatarios)"class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-[#2447F9] hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"><Send :size="13" /></button>
      <button @click="emit('duplicar')" title="Duplicar" class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-[#2447F9] hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"><Copy :size="13" /></button>
      <button @click="descargar" title="Descargar HTML" class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-[#2447F9] hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"><Download :size="13" /></button>
      <button @click="emit('eliminar')" title="Eliminar" class="w-8 h-8 rounded-lg border border-default bg-white dark:bg-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-red-500 hover:border-red-200 dark:hover:border-red-900 transition-all"><Trash2 :size="13" /></button>
    </div>
  </div>
</template>
