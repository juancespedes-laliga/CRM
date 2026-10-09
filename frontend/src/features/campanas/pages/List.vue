<script setup lang="ts">
import { ref, computed } from 'vue'
import { Plus } from 'lucide-vue-next'
import type { Plantilla, PlantillaDraft } from '../types/plantilla'
import { usePlantillas } from '../composables/usePlantillas'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue'
import PlantillaListItem from '../components/PlantillaListItem.vue'
import EditorPlantillaDialog from '../dialogs/EditorPlantillaDialog.vue'
import EnviarPlantillaDialog from '../dialogs/EnviarPlantillaDialog.vue'

// "gestionar" cubre crear y editar; no hay accion "eliminar" real en backend.
const { gestionar: puedeGestionar } = permisosDeModulo('campanas')
const { plantillas, crear, actualizar, duplicar, eliminar } = usePlantillas()

const editorPlantillaVisible = ref(false)
const plantillaEditando = ref<Plantilla | null>(null)
// Última plantilla creada/guardada: define a quién actualizar y qué enviar.
const plantillaGuardada = ref<Plantilla | null>(null)

const abrirEditorPlantilla = (p: Plantilla | null) => {
  plantillaEditando.value = p
  plantillaGuardada.value = p
  editorPlantillaVisible.value = true
}

const guardarPlantilla = async (d: PlantillaDraft) => {
  const p = plantillaEditando.value
    ? await actualizar(plantillaEditando.value.id, d)
    : await crear(d)
  if (p) {
    plantillaEditando.value = p   // pasa a modo "editar" tras el primer guardado
    plantillaGuardada.value = p
  }
}

const enviarVisible = ref(false)
const payloadEnvio = computed(() =>
  plantillaGuardada.value
    ? { nombre: plantillaGuardada.value.nombre, asunto: plantillaGuardada.value.asunto, html: plantillaGuardada.value.html }
    : null,
)
const abrirEnvio = (p: Plantilla) => { plantillaGuardada.value = p; enviarVisible.value = true }
// El boton "Enviar" del editor guarda (espera a que quede en la BD) y solo
// despues abre el dialogo de envio, para no mandar una version vieja.
const onEnviarDesdeEditor = async (d: PlantillaDraft) => {
  await guardarPlantilla(d)
  enviarVisible.value = true
}

// Eliminar
const confirmEliminarVisible = ref(false)
const plantillaAEliminar = ref<Plantilla | null>(null)
const pedirEliminar = (p: Plantilla) => { plantillaAEliminar.value = p; confirmEliminarVisible.value = true }
const confirmarEliminar = () => {
  if (plantillaAEliminar.value) eliminar(plantillaAEliminar.value.id)
  plantillaAEliminar.value = null
}
</script>

<template>
  <div class="space-y-5 font-[Inter,system-ui,sans-serif]">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-[18px] font-bold text-heading flex items-center gap-2">
          Campañas
          <span class="bg-[#EEF2FF] dark:bg-blue-950/50 text-slate-900 dark:text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full">
            {{ plantillas.length }}
          </span>
        </h2>
        <p class="text-[12px] text-body mt-0.5">Plantillas de correo con editor visual</p>
      </div>
      <button
        v-if="puedeGestionar"
        @click="abrirEditorPlantilla(null)"
        class="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all"
      >
        <Plus :size="14" /> Nueva plantilla
      </button>
    </div>

    <div class="surface-card rounded-2xl shadow-sm overflow-hidden">
      <div class="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
        <h3 class="text-[13px] font-bold text-heading">Plantillas de correo</h3>
        <p class="text-[11px] text-muted mt-0.5">Se guardan en este navegador. Edítalas con el editor visual, descárgalas o envíalas.</p>
      </div>
      <div v-if="plantillas.length" class="divide-y divide-slate-100 dark:divide-slate-700">
        <PlantillaListItem
          v-for="p in plantillas"
          :key="p.id"
          :plantilla="p"
          @editar="abrirEditorPlantilla(p)"
          @enviar="abrirEnvio(p)"
          @duplicar="duplicar(p.id)"
          @eliminar="pedirEliminar(p)"
        />
      </div>
      <div v-else class="px-5 py-12 text-center text-[12px] text-muted">
        Aún no hay plantillas. Crea la primera con “Nueva plantilla”.
      </div>
    </div>

    <EditorPlantillaDialog
      v-model:visible="editorPlantillaVisible"
      :plantilla="plantillaEditando"
      @submit="guardarPlantilla"
      @enviar="onEnviarDesdeEditor"
    />
    <EnviarPlantillaDialog v-model:visible="enviarVisible" :plantilla="payloadEnvio" />

    <ConfirmDialog
      v-model:visible="confirmEliminarVisible"
      titulo="Eliminar plantilla"
      :mensaje="`Se eliminará la plantilla “${plantillaAEliminar?.nombre ?? ''}”. Esta acción no se puede deshacer.`"
      texto-confirmar="Eliminar"
      texto-cancelar="Cancelar"
      @confirmar="confirmarEliminar"
    />
  </div>
</template>
