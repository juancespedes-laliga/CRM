<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Select from 'primevue/select'
import type { BeneficiarioDraft } from '../types/plan-liga'
import { beneficiarioSchema } from '../schemas/beneficiario.schema'
import { useZodForm } from '@/shared/composables/useZodForm'
import { useNombreCompuesto } from '@/shared/composables/useNombreCompuesto'
import { faltaApellido } from '@/shared/utils/nombreCompuesto'
import { fieldStateClass } from '@/shared/utils/fieldStateClass'
import { useUbicaciones } from '@/shared/composables/useUbicaciones'
import { TIPOS_DOCUMENTO_OPCIONES } from '@/shared/constants/tiposDocumento'
import FieldError from '@/shared/components/FieldError.vue'
import FechaInput from '@/shared/components/FechaInput.vue'

const props = defineProps<{ modo?: 'nuevo' | 'editar' }>()
const draft = defineModel<BeneficiarioDraft>({ required: true })
const emit = defineEmits<{ validSubmit: [] }>()

const { errors, tocar, esVisible, onValidSubmit } = useZodForm(beneficiarioSchema, draft)
const nombre = useNombreCompuesto(draft, 'nombre')
const apellidoFaltante = computed(() => faltaApellido(nombre))

const { departamentos, municipios, cargandoUbicaciones, municipiosDeDepartamento } = useUbicaciones()
const municipiosDisponibles = computed(() => draft.value.departamento ? municipiosDeDepartamento(draft.value.departamento) : [])
// Ver el comentario equivalente en TitularForm.vue: no tocar la ciudad mientras el catálogo de
// municipios todavía no ha cargado, para no borrar la ciudad de un beneficiario que se está
// editando antes de que el catálogo llegue a tiempo.
watch(() => draft.value.departamento, (nuevo, anterior) => {
  if (nuevo === anterior || !draft.value.ciudad || municipios.value.length === 0) return
  if (!municipiosDeDepartamento(nuevo).some(m => m.codigo === draft.value.ciudad)) draft.value.ciudad = ''
})

defineExpose({ submit: onValidSubmit(() => { if (!apellidoFaltante.value) emit('validSubmit') }) })

// Fecha de inscripción y estado quedan fijados al crear el beneficiario: se muestran
// de solo lectura en edición para evitar registrar cambios que nunca se guardan.
// El estado solo se cambia desde el botón de desactivar en la lista de beneficiarios.
const soloLecturaEnEdicion = computed(() => props.modo === 'editar')

// Ver el comentario equivalente en TitularForm.vue.
const tienePlanSalud = ref(!!draft.value.planSalud || !!draft.value.planNombre)
watch(tienePlanSalud, (v) => { if (!v) { draft.value.planSalud = ''; draft.value.planNombre = '' } })
</script>

<template>
  <div class="space-y-6">
    <div>
      <h4 class="text-[10px] font-bold text-[#EC4899] uppercase tracking-wider pb-2 mb-1 border-b border-slate-100 dark:border-slate-700">Identificación</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Nombre completo *</label>
          <div class="grid grid-cols-2 gap-3">
            <input v-model="nombre.nombre1" @blur="tocar('nombre')" placeholder="Primer nombre" class="w-full h-10 px-4 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:bg-white dark:focus:bg-slate-800 transition-all" :class="fieldStateClass(esVisible('nombre') && (!!errors.nombre || apellidoFaltante), esVisible('nombre') && !errors.nombre && !apellidoFaltante && !!draft.nombre, 'border-slate-200 dark:border-slate-600 focus:border-[#EC4899]')" />
            <input v-model="nombre.nombre2" @blur="tocar('nombre')" placeholder="Segundo nombre" class="w-full h-10 px-4 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:bg-white dark:focus:bg-slate-800 transition-all" :class="fieldStateClass(esVisible('nombre') && (!!errors.nombre || apellidoFaltante), esVisible('nombre') && !errors.nombre && !apellidoFaltante && !!draft.nombre, 'border-slate-200 dark:border-slate-600 focus:border-[#EC4899]')" />
            <input v-model="nombre.apellido1" @blur="tocar('nombre')" placeholder="Primer apellido" class="w-full h-10 px-4 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:bg-white dark:focus:bg-slate-800 transition-all" :class="fieldStateClass(esVisible('nombre') && (!!errors.nombre || apellidoFaltante), esVisible('nombre') && !errors.nombre && !apellidoFaltante && !!draft.nombre, 'border-slate-200 dark:border-slate-600 focus:border-[#EC4899]')" />
            <input v-model="nombre.apellido2" @blur="tocar('nombre')" placeholder="Segundo apellido" class="w-full h-10 px-4 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:bg-white dark:focus:bg-slate-800 transition-all" :class="fieldStateClass(esVisible('nombre') && (!!errors.nombre || apellidoFaltante), esVisible('nombre') && !errors.nombre && !apellidoFaltante && !!draft.nombre, 'border-slate-200 dark:border-slate-600 focus:border-[#EC4899]')" />
          </div>
          <FieldError :message="esVisible('nombre') ? (apellidoFaltante ? 'Falta el apellido: mínimo un nombre y un apellido' : errors.nombre) : undefined" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Tipo de documento *</label>
          <Select v-model="draft.tipoDocumento" @change="tocar('tipoDocumento')" :options="TIPOS_DOCUMENTO_OPCIONES" option-label="label" option-value="value"
            filter filter-placeholder="Buscar tipo..." placeholder="Selecciona un tipo de documento"
            empty-filter-message="Sin resultados" class="w-full" input-class="h-10 text-[12px] flex items-center"
            :class="fieldStateClass(esVisible('tipoDocumento') && !!errors.tipoDocumento, esVisible('tipoDocumento') && !errors.tipoDocumento && !!draft.tipoDocumento, '')" />
          <FieldError :message="esVisible('tipoDocumento') ? errors.tipoDocumento : undefined" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Documento *</label>
          <input v-model="draft.documento" @blur="tocar('documento')" placeholder="Número de documento" class="w-full h-10 px-4 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:bg-white dark:focus:bg-slate-800 transition-all" :class="fieldStateClass(esVisible('documento') && !!errors.documento, esVisible('documento') && !errors.documento && !!draft.documento, 'border-slate-200 dark:border-slate-600 focus:border-[#EC4899]')" />
          <FieldError :message="esVisible('documento') ? errors.documento : undefined" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Fecha de nacimiento *</label>
          <FechaInput v-model="draft.fechaNacimiento" @blur="tocar('fechaNacimiento')"
            :invalid="esVisible('fechaNacimiento') && !!errors.fechaNacimiento"
            :valid="esVisible('fechaNacimiento') && !errors.fechaNacimiento && !!draft.fechaNacimiento" />
          <FieldError :message="esVisible('fechaNacimiento') ? errors.fechaNacimiento : undefined" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Sexo biológico</label>
          <select v-model="draft.sexo" class="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all cursor-pointer">
            <option value="">Sin especificar</option>
            <option value="Masculino">Masculino</option>
            <option value="Femenino">Femenino</option>
          </select>
        </div>
      </div>
    </div>

    <div>
      <h4 class="text-[10px] font-bold text-[#EC4899] uppercase tracking-wider pb-2 mb-4 border-b border-slate-100 dark:border-slate-700">Contacto</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Correo</label>
          <input v-model="draft.correo" @blur="tocar('correo')" type="email" placeholder="correo@ejemplo.com" class="w-full h-10 px-4 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:bg-white dark:focus:bg-slate-800 transition-all" :class="fieldStateClass(esVisible('correo') && !!errors.correo, esVisible('correo') && !errors.correo && !!draft.correo, 'border-slate-200 dark:border-slate-600 focus:border-[#EC4899]')" />
          <FieldError :message="esVisible('correo') ? errors.correo : undefined" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Teléfono</label>
          <input v-model="draft.telefono" @blur="tocar('telefono')" placeholder="300-000-0000" class="w-full h-10 px-4 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:bg-white dark:focus:bg-slate-800 transition-all" :class="fieldStateClass(esVisible('telefono') && !!errors.telefono, esVisible('telefono') && !errors.telefono && !!draft.telefono, 'border-slate-200 dark:border-slate-600 focus:border-[#EC4899]')" />
          <FieldError :message="esVisible('telefono') ? errors.telefono : undefined" />
        </div>
      </div>
    </div>

    <div>
      <h4 class="text-[10px] font-bold text-[#EC4899] uppercase tracking-wider pb-2 mb-4 border-b border-slate-100 dark:border-slate-700">Ubicación</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Dirección</label>
          <input v-model="draft.direccion" placeholder="Dirección de residencia" class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Departamento *</label>
          <Select v-model="draft.departamento" @change="tocar('departamento')" :options="departamentos" option-label="nombre" option-value="codigo"
            filter filter-placeholder="Buscar departamento..." :loading="cargandoUbicaciones" placeholder="Selecciona un departamento"
            empty-filter-message="Sin resultados" empty-message="Sin departamentos" class="w-full" input-class="h-10 text-[12px] flex items-center"
            :class="fieldStateClass(esVisible('departamento') && !!errors.departamento, esVisible('departamento') && !errors.departamento && !!draft.departamento, '')" />
          <FieldError :message="esVisible('departamento') ? errors.departamento : undefined" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Ciudad *</label>
          <Select v-model="draft.ciudad" @change="tocar('ciudad')" :options="municipiosDisponibles" option-label="nombre" option-value="codigo"
            filter filter-placeholder="Buscar municipio..." :disabled="!draft.departamento" :loading="cargandoUbicaciones"
            :placeholder="draft.departamento ? 'Selecciona un municipio' : 'Elige primero un departamento'"
            empty-filter-message="Sin resultados" empty-message="Sin municipios" class="w-full" input-class="h-10 text-[12px] flex items-center"
            :class="fieldStateClass(esVisible('ciudad') && !!errors.ciudad, esVisible('ciudad') && !errors.ciudad && !!draft.ciudad, '')" />
          <FieldError :message="esVisible('ciudad') ? errors.ciudad : undefined" />
        </div>
        <div class="sm:col-span-2">
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Empresa</label>
          <input v-model="draft.empresa" placeholder="Nombre empresa (si aplica)" class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
      </div>
    </div>

    <div>
      <h4 class="text-[10px] font-bold text-[#EC4899] uppercase tracking-wider pb-2 mb-4 border-b border-slate-100 dark:border-slate-700">Plan</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Tipo de plan</label>
          <input v-model="draft.tipoPlan" placeholder="Ej: Plan Familiar, Plan Individual" class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">EPS</label>
          <input v-model="draft.eps" placeholder="Nombre de la EPS" class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Otra EPS</label>
          <input v-model="draft.otraEps" placeholder="Solo si la EPS no está en la lista" class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all" />
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">¿Tiene plan complementario de salud?</label>
          <div class="flex gap-2">
            <button type="button" @click="tienePlanSalud = true"
              class="h-10 px-4 rounded-lg border text-[12px] font-semibold transition-all"
              :class="tienePlanSalud ? 'bg-[#EC4899] border-[#EC4899] text-white' : 'border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 hover:border-slate-300'"
            >Sí</button>
            <button type="button" @click="tienePlanSalud = false"
              class="h-10 px-4 rounded-lg border text-[12px] font-semibold transition-all"
              :class="!tienePlanSalud ? 'bg-[#EC4899] border-[#EC4899] text-white' : 'border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 hover:border-slate-300'"
            >No</button>
          </div>
        </div>
        <template v-if="tienePlanSalud">
          <div>
            <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Plan de salud</label>
            <input v-model="draft.planSalud" placeholder="Ej: Medicina prepagada, Póliza de salud" class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all" />
          </div>
          <div class="sm:col-span-2">
            <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Nombre del plan</label>
            <input v-model="draft.planNombre" placeholder="Nombre comercial del plan" class="w-full h-10 px-4 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all" />
          </div>
        </template>
      </div>
    </div>

    <div>
      <h4 class="text-[10px] font-bold text-[#EC4899] uppercase tracking-wider pb-2 mb-4 border-b border-slate-100 dark:border-slate-700">Estado</h4>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Estado</label>
          <select v-model="draft.estado" :disabled="soloLecturaEnEdicion" title="Usa el botón de desactivar en la lista de beneficiarios para cambiar el estado" class="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-[12px] outline-none focus:border-[#EC4899] focus:bg-white dark:focus:bg-slate-800 transition-all cursor-pointer disabled:bg-slate-100 dark:disabled:bg-slate-800 disabled:text-slate-400 dark:disabled:text-slate-500 disabled:cursor-not-allowed">
            <option value="Activo">Activo</option>
            <option value="Inactivo">Inactivo</option>
            <option value="Reemplazado">Reemplazado</option>
            <option value="Retirado">Retirado</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1.5 uppercase tracking-wide">Fecha inscripción</label>
          <FechaInput v-model="draft.fechaInscripcion" disabled placeholder="Se hereda del titular" title="Se hereda automáticamente de la fecha de ingreso del titular" />
        </div>
      </div>
    </div>
  </div>
</template>
