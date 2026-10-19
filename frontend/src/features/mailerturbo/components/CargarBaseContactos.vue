<script setup lang="ts">
import { ref } from 'vue'
import { Upload, FileSpreadsheet, RefreshCw, Download, AlertTriangle, Loader2 } from 'lucide-vue-next'
import type { ContactoMT } from '../types/mailerturbo'
import { descargarPlantillaBaseContactos, leerBaseContactos, type LecturaBaseContactos } from '../utils/baseContactos'

// Zona para soltar un Excel/CSV con la base de contactos. Expone los contactos
// válidos por v-model; el resumen (descartados, duplicados) se muestra aquí mismo.
const contactos = defineModel<ContactoMT[]>({ required: true })

const nf = new Intl.NumberFormat('es-CO')
const archivo = ref<File | null>(null)
const lectura = ref<LecturaBaseContactos | null>(null)
const leyendo = ref(false)
const error = ref<string | null>(null)
const dragOver = ref(false)
const verDescartados = ref(false)
const verVistaPrevia = ref(false)
const FILAS_VISTA_PREVIA = 8
const fileInput = ref<HTMLInputElement | null>(null)

const EXTENSIONES = ['.xlsx', '.xls', '.csv']

async function procesar(file: File) {
  if (!EXTENSIONES.some(ext => file.name.toLowerCase().endsWith(ext))) {
    error.value = 'Formato no soportado. Use .xlsx, .xls o .csv.'
    return
  }
  archivo.value = file
  leyendo.value = true
  error.value = null
  lectura.value = null
  contactos.value = []
  try {
    lectura.value = await leerBaseContactos(file)
    contactos.value = lectura.value.validos
    if (!lectura.value.validos.length) error.value = 'El archivo no tiene contactos con correo válido.'
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'No se pudo leer el archivo.'
  } finally {
    leyendo.value = false
  }
}

const onDrop = (e: DragEvent) => {
  dragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file) void procesar(file)
}
const onFileInput = (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) void procesar(file)
  input.value = '' // permite volver a elegir el mismo archivo
}
const limpiar = () => {
  archivo.value = null
  lectura.value = null
  error.value = null
  contactos.value = []
}
</script>

<template>
  <div class="space-y-2">
    <div
      class="border-2 border-dashed rounded-xl px-4 py-5 text-center transition-all cursor-pointer"
      :class="dragOver ? 'border-[#2447F9] bg-[#EEF2FF] dark:bg-blue-950/40'
        : lectura?.validos.length ? 'border-emerald-400 dark:border-emerald-600 bg-emerald-50 dark:bg-emerald-950/40'
          : 'border-slate-300 dark:border-slate-600 hover:border-[#2447F9] hover:bg-[#EEF2FF]/30 dark:hover:bg-blue-950/20'"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="onDrop"
      @click="fileInput?.click()"
    >
      <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" class="hidden" @change="onFileInput" />

      <div v-if="leyendo" class="flex items-center justify-center gap-2 text-[12px] text-muted">
        <Loader2 :size="14" class="animate-spin" /> Leyendo archivo…
      </div>
      <div v-else-if="!archivo">
        <Upload :size="20" class="text-[#2447F9] dark:text-blue-400 mx-auto mb-2" />
        <p class="text-[12px] font-bold text-heading">Arrastra la base de contactos o haz clic para elegirla</p>
        <p class="text-[10px] text-muted mt-0.5">.xlsx · .xls · .csv — columnas NOMBRE, APELLIDO, CORREO, TELEFONO</p>
      </div>
      <div v-else class="flex items-center justify-center gap-3 text-left">
        <FileSpreadsheet :size="22" class="text-emerald-600 dark:text-emerald-400 shrink-0" />
        <div class="min-w-0">
          <p class="text-[12px] font-bold text-heading truncate">{{ archivo.name }}</p>
          <p v-if="lectura" class="text-[11px] text-muted">
            <strong class="text-heading tabular-nums">{{ nf.format(lectura.validos.length) }}</strong> contactos válidos
            <template v-if="lectura.duplicados"> · {{ nf.format(lectura.duplicados) }} duplicados</template>
            <template v-if="lectura.descartados.length"> · {{ nf.format(lectura.descartados.length) }} descartados</template>
          </p>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between text-[11px]">
      <button type="button" class="flex items-center gap-1 font-semibold text-muted hover:text-[#2447F9]" @click="descargarPlantillaBaseContactos">
        <Download :size="12" /> Descargar plantilla de ejemplo
      </button>
      <button v-if="archivo" type="button" class="flex items-center gap-1 font-semibold text-muted hover:text-[#2447F9]" @click="limpiar">
        <RefreshCw :size="12" /> Cambiar archivo
      </button>
    </div>

    <div v-if="lectura?.validos.length" class="rounded-lg border border-default overflow-hidden">
      <button type="button" class="w-full flex items-center justify-between px-3 h-8 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-800" @click="verVistaPrevia = !verVistaPrevia">
        <span>{{ verVistaPrevia ? 'Ocultar' : 'Ver' }} contactos del archivo</span>
        <span class="text-muted font-normal">{{ nf.format(lectura.validos.length) }}</span>
      </button>
      <div v-if="verVistaPrevia" class="overflow-x-auto border-t border-default">
        <table class="w-full text-[11px]">
          <thead>
            <tr class="text-left text-[10px] uppercase tracking-wide text-subtle border-b border-default">
              <th class="px-3 py-1.5 font-semibold">Nombre</th>
              <th class="px-3 py-1.5 font-semibold">Correo</th>
              <th class="px-3 py-1.5 font-semibold">Teléfono</th>
              <th class="px-3 py-1.5 font-semibold">Ciudad</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in lectura.validos.slice(0, FILAS_VISTA_PREVIA)" :key="c.correo" class="border-b border-slate-100 dark:border-slate-800 last:border-0">
              <td class="px-3 py-1.5 text-heading whitespace-nowrap">{{ [c.nombre, c.apellido].filter(Boolean).join(' ') }}</td>
              <td class="px-3 py-1.5 text-body">{{ c.correo }}</td>
              <td class="px-3 py-1.5 tabular-nums" :class="c.telefono ? 'text-body' : 'text-amber-600 dark:text-amber-400'">{{ c.telefono || 'Sin teléfono' }}</td>
              <td class="px-3 py-1.5 text-muted">{{ c.ciudad || '—' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="lectura.validos.length > FILAS_VISTA_PREVIA" class="px-3 py-1.5 text-[10px] text-muted border-t border-default">
          …y {{ nf.format(lectura.validos.length - FILAS_VISTA_PREVIA) }} más
        </p>
      </div>
    </div>

    <div v-if="error" class="rounded-lg bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 text-[11px] font-semibold px-3 py-2">{{ error }}</div>

    <div v-if="lectura && (lectura.sinTelefono || lectura.descartados.length)" class="rounded-lg border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-3 py-2 text-[11px] text-amber-700 dark:text-amber-300 space-y-1">
      <div v-if="lectura.sinTelefono" class="flex items-start gap-1.5">
        <AlertTriangle :size="12" class="mt-0.5 shrink-0" />
        <span>{{ nf.format(lectura.sinTelefono) }} contacto(s) sin teléfono: MailerTurbo podría rechazarlos al crear la campaña.</span>
      </div>
      <div v-if="lectura.descartados.length">
        <button type="button" class="font-semibold underline" @click="verDescartados = !verDescartados">
          {{ verDescartados ? 'Ocultar' : 'Ver' }} filas descartadas ({{ lectura.descartados.length }})
        </button>
        <ul v-if="verDescartados" class="mt-1 max-h-24 overflow-y-auto space-y-0.5">
          <li v-for="d in lectura.descartados" :key="d.fila">Fila {{ d.fila }} — {{ d.motivo }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>
