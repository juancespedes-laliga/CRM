<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { OportunidadDraft, TipoCliente } from '../types/oportunidad'
import { ETAPAS, TIPOS_CLIENTE } from '../constants/oportunidades.constants'
import { oportunidadSchema } from '../schemas/oportunidad.schema'
import { useZodForm } from '@/shared/composables/useZodForm'
import { fieldStateClass } from '@/shared/utils/fieldStateClass'
import FieldError from '@/shared/components/FieldError.vue'
import BuscadorEntidad, { type OpcionBuscador } from '@/shared/components/BuscadorEntidad.vue'
import { getEmpresas } from '@/features/empresas/services/empresas.api'
import type { Empresa } from '@/features/empresas/types/empresa'
import { getContactos } from '@/features/contactos/services/contactos.api'
import type { Contacto } from '@/features/contactos/types/contacto'
import { getListadoTitulares } from '@/features/plan-liga/services/plan-liga.api'
import { getServicios } from '@/features/servicios/services/servicios.api'

const draft = defineModel<OportunidadDraft>({ required: true })
const emit = defineEmits<{ validSubmit: [] }>()

const { errors, tocar, esVisible, onValidSubmit } = useZodForm(oportunidadSchema, draft)
defineExpose({ submit: onValidSubmit(() => emit('validSubmit')) })

const empresas = ref<Empresa[]>([])
onMounted(async () => { empresas.value = await getEmpresas() })

const opcionesEmpresas = computed<OpcionBuscador[]>(() =>
  empresas.value.map(e => ({ id: e.id, label: e.razonSocial, sublabel: e.ciudad })),
)

const contactos = ref<Contacto[]>([])
onMounted(async () => { contactos.value = await getContactos() })

const servicios = ref<string[]>([])
onMounted(async () => { servicios.value = await getServicios() })

const opcionesContactos = computed<OpcionBuscador[]>(() =>
  contactos.value.map(c => ({ id: c.id, label: c.nombre, sublabel: c.empresaNombre })),
)

const opcionesContactosDeEmpresa = computed<OpcionBuscador[]>(() => {
  if (draft.value.empresaId === null) return []
  return contactos.value
    .filter(c => c.empresaId === draft.value.empresaId)
    .map(c => ({ id: c.id, label: c.nombre, sublabel: c.cargo }))
})

// Los titulares Plan Liga pueden ser miles: se busca contra el backend a medida que se
// escribe en vez de precargar el catálogo completo (ver mismo ajuste en ActividadForm).
async function buscarTitulares(query: string): Promise<OpcionBuscador[]> {
  const { items } = await getListadoTitulares({ busqueda: query || undefined, limit: 8 })
  return items.map(t => ({ id: t.id, label: t.nombre, sublabel: t.empresa }))
}

function cambiarTipoCliente(tipo: TipoCliente) {
  if (draft.value.tipoCliente === tipo) return
  draft.value.tipoCliente = tipo
  draft.value.empresaId = null
  draft.value.empresaNombre = ''
  draft.value.contactoId = null
  draft.value.contactoNombre = ''
  draft.value.planLigaTitularId = null
  draft.value.titularNombre = ''
}

function alSeleccionarEmpresa(item: OpcionBuscador | null) {
  draft.value.empresaNombre = item?.label ?? ''
  draft.value.contactoId = null
  draft.value.contactoNombre = ''
}

function alSeleccionarContacto(item: OpcionBuscador | null) {
  draft.value.contactoNombre = item?.label ?? ''
}

function alSeleccionarTitular(item: OpcionBuscador | null) {
  draft.value.titularNombre = item?.label ?? ''
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <div class="sm:col-span-2">
      <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Tipo de cliente *</label>
      <div class="grid grid-cols-3 gap-1.5 p-1 bg-slate-100 dark:bg-slate-900 rounded-lg">
        <button
          v-for="t in TIPOS_CLIENTE" :key="t.value" type="button"
          @click="cambiarTipoCliente(t.value)"
          class="h-9 rounded-md text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all"
          :class="draft.tipoCliente === t.value ? 'bg-white dark:bg-slate-700 text-slate-900 font-bold dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
        >
          <component :is="t.icono" :size="13" />
          <span class="truncate">{{ t.label }}</span>
        </button>
      </div>
    </div>

    <template v-if="draft.tipoCliente === 'empresa'">
      <div class="sm:col-span-2">
        <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Empresa *</label>
        <BuscadorEntidad
          v-model="draft.empresaId"
          :opciones="opcionesEmpresas"
          placeholder="Buscar empresa..."
          vacio="No se encontraron empresas"
          @select="alSeleccionarEmpresa"
          @blur="tocar('empresaId')"
        />
        <FieldError :message="esVisible('empresaId') ? errors.empresaId : undefined" />
      </div>
      <div class="sm:col-span-2">
        <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Contacto (opcional)</label>
        <BuscadorEntidad
          v-model="draft.contactoId"
          :opciones="opcionesContactosDeEmpresa"
          :disabled="!draft.empresaId"
          placeholder="Buscar contacto de la empresa..."
          vacio="Esta empresa no tiene contactos registrados"
          @select="alSeleccionarContacto"
        />
      </div>
    </template>

    <template v-else-if="draft.tipoCliente === 'contacto'">
      <div class="sm:col-span-2">
        <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Contacto *</label>
        <BuscadorEntidad
          v-model="draft.contactoId"
          :opciones="opcionesContactos"
          placeholder="Buscar contacto..."
          vacio="No se encontraron contactos"
          @select="alSeleccionarContacto"
          @blur="tocar('contactoId')"
        />
        <FieldError :message="esVisible('contactoId') ? errors.contactoId : undefined" />
      </div>
    </template>

    <template v-else-if="draft.tipoCliente === 'titular'">
      <div class="sm:col-span-2">
        <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Titular Plan Liga *</label>
        <BuscadorEntidad
          v-model="draft.planLigaTitularId"
          :opciones="[]"
          :buscar="buscarTitulares"
          :label-seleccionado="draft.titularNombre"
          placeholder="Buscar titular Plan Liga..."
          vacio="No se encontraron titulares"
          @select="alSeleccionarTitular"
          @blur="tocar('planLigaTitularId')"
        />
        <FieldError :message="esVisible('planLigaTitularId') ? errors.planLigaTitularId : undefined" />
      </div>
    </template>

    <div class="sm:col-span-2">
      <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Servicio *</label>
      <select v-model="draft.servicio" @blur="tocar('servicio')" class="w-full h-10 px-3 rounded-lg border bg-slate-50 dark:bg-slate-900 text-[12px] text-slate-900 dark:text-slate-100 outline-none focus:bg-white dark:focus:bg-slate-800 transition-all cursor-pointer" :class="fieldStateClass(esVisible('servicio') && !!errors.servicio, esVisible('servicio') && !errors.servicio && !!draft.servicio, 'border-slate-200 dark:border-slate-600 focus:border-[#2447F9]')">
        <option value="">Seleccionar servicio</option>
        <option v-for="s in servicios" :key="s" :value="s">{{ s }}</option>
      </select>
      <FieldError :message="esVisible('servicio') ? errors.servicio : undefined" />
    </div>
    <div>
      <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Valor</label>
      <input v-model="draft.valor" placeholder="$0" class="w-full h-10 px-4 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all" />
    </div>
    <div>
      <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Probabilidad ({{ draft.probabilidad }}%)</label>
      <input v-model.number="draft.probabilidad" type="range" min="0" max="100" step="5" class="w-full h-2 rounded-lg appearance-none cursor-pointer mt-3" />
    </div>
    <div class="sm:col-span-2">
      <label class="block text-[11px] font-bold text-body mb-1.5 uppercase tracking-wide">Etapa</label>
      <select v-model="draft.estado" class="w-full h-10 px-3 rounded-lg input-surface text-[12px] outline-none focus:border-[#2447F9] focus:bg-white dark:focus:bg-slate-800 transition-all cursor-pointer">
        <option v-for="e in ETAPAS" :key="e" :value="e">{{ e }}</option>
      </select>
    </div>
  </div>
</template>
