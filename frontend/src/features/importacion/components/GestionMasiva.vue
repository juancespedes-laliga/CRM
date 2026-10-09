<script setup lang="ts">
import { ref, computed } from 'vue'

// --- INTERFACES ---
interface Beneficiario {
  nombreCompleto: string
  tipoDocumento: string
  documento: string
  edad: number
  genero: string
  parentesco: string
  activo?: boolean
}

interface Contacto {
  idUnico: string
  nombreCompleto: string
  rol: 'titular' | 'beneficiario'
  activo?: boolean
  beneficiariosAsociados?: Beneficiario[]
}

// --- PROPS & EMITS ---
const props = defineProps<{
  contacto: Contacto
}>()

const emit = defineEmits(['update:contacto'])

// --- ESTADOS ---
const des_control_estado = ref(true)
const des_vinculacion = ref(false)

// --- ESTADO FORMULARIO VINCULAR BENEFICIARIO Express ---
const nuevoBeneficiario = ref<Beneficiario>({
  nombreCompleto: '',
  tipoDocumento: 'CC',
  documento: '',
  edad: 18,
  genero: 'Masculino',
  parentesco: 'Hijo(a)',
  activo: true
})

const totalMiembros = computed(() => {
  return 1 + (props.contacto.beneficiariosAsociados?.length || 0)
})

const resetFormulario = () => {
  nuevoBeneficiario.value = {
    nombreCompleto: '',
    tipoDocumento: 'CC',
    documento: '',
    edad: 18,
    genero: 'Masculino',
    parentesco: 'Hijo(a)',
    activo: true
  }
}

const ejecutarVinculacion = () => {
  if (
    !nuevoBeneficiario.value.nombreCompleto ||
    !nuevoBeneficiario.value.documento
  ) {
    alert('Por favor, completa los campos requeridos (Nombre y Documento).')
    return
  }

  if (totalMiembros.value >= 5) {
    alert('Límite familiar alcanzado (Máximo 5 miembros por núcleo).')
    return
  }

  const contactoActualizado = { ...props.contacto }

  if (!contactoActualizado.beneficiariosAsociados) {
    contactoActualizado.beneficiariosAsociados = []
  }

  contactoActualizado.beneficiariosAsociados.push({
    ...nuevoBeneficiario.value
  })

  emit('update:contacto', contactoActualizado)

  resetFormulario()
}
</script>

<template>
  <div
    class="space-y-3 animate-fadeIn font-semibold text-xs text-slate-700 dark:text-slate-300 max-w-sm mx-auto"
  >
    <!-- CONTROL ESTADO -->
    <div
      class="border border-slate-200/80 dark:border-slate-700 rounded-xl overflow-hidden bg-white dark:bg-slate-800 shadow-2xs"
    >
      <button
        @click="des_control_estado = !des_control_estado"
        class="w-full flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100/70 dark:hover:bg-slate-700/70 transition-colors text-left cursor-pointer"
      >
        <span
          class="text-[10px] font-black text-subtle uppercase tracking-wider"
        >
          Control de Estado Operativo
        </span>

        <span
          class="text-slate-400 dark:text-slate-500 text-[10px] transform transition-transform duration-200"
          :class="des_control_estado ? 'rotate-180' : ''"
        >
          ▼
        </span>
      </button>

      <div
        v-show="des_control_estado"
        class="p-2.5 border-t border-slate-100 dark:border-slate-700 max-h-60 overflow-y-auto scrollbar-thin space-y-3"
      >
        <!-- TITULAR -->
        <div
          class="flex items-center justify-between pb-2.5 border-b border-slate-100 dark:border-slate-700"
        >
          <div class="min-w-0 pr-2">
            <span
              class="text-[8px] uppercase bg-blue-100 dark:bg-blue-900/60 text-slate-900 dark:text-white border border-blue-200 dark:border-blue-800 px-1.5 py-0.5 rounded font-black tracking-wider"
            >
              Titular de Cuenta
            </span>

            <p class="text-xs font-black text-heading truncate mt-1">
              {{ props.contacto.nombreCompleto }}
            </p>
          </div>

          <div class="flex flex-col items-end gap-1 select-none">
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                v-model="props.contacto.activo"
                class="sr-only peer"
              />

              <div
                class="w-8 h-4.5 bg-slate-300 dark:bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 dark:after:border-slate-600 after:border after:rounded-full after:h-3.5 after:w-3.5 after:transition-all peer-checked:bg-emerald-500"
              ></div>
            </label>

            <span
              class="text-[8px] font-black tracking-tight uppercase"
              :class="
                props.contacto.activo
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-slate-400 dark:text-slate-500'
              "
            >
              {{ props.contacto.activo ? 'Activo' : 'Desactivado' }}
            </span>
          </div>
        </div>

        <!-- BENEFICIARIOS -->
        <div
          v-if="
            props.contacto.beneficiariosAsociados &&
            props.contacto.beneficiariosAsociados.length > 0
          "
          class="space-y-1.5"
        >
          <span
            class="text-[8px] uppercase font-black tracking-widest text-muted block mb-1"
          >
            Beneficiarios del Núcleo
          </span>

          <div
            v-for="(benefic, idx) in props.contacto.beneficiariosAsociados"
            :key="idx"
            class="flex items-center justify-between surface-sunken p-2 border border-slate-200/60 dark:border-slate-700 rounded-lg shadow-3xs"
          >
            <div class="min-w-0 pr-2">
              <p class="text-[10px] font-black text-body truncate">
                {{ benefic.nombreCompleto }}
              </p>

              <span class="text-[8px] text-muted font-medium">
                {{ benefic.parentesco }}
              </span>
            </div>

            <div class="flex flex-col items-end gap-0.5 select-none">
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  v-model="benefic.activo"
                  class="sr-only peer"
                />

                <div
                  class="w-7 h-4 bg-slate-300 dark:bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 dark:after:border-slate-600 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-emerald-500"
                ></div>
              </label>

              <span
                class="text-[7px] font-black tracking-tight uppercase"
                :class="
                  benefic.activo
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-slate-400 dark:text-slate-500'
                "
              >
                {{ benefic.activo ? 'Activo' : 'Desactivado' }}
              </span>
            </div>
          </div>
        </div>

        <div
          v-else
          class="text-[10px] text-muted italic text-center py-2 font-medium"
        >
          No hay beneficiarios asignados a esta cuenta.
        </div>
      </div>
    </div>

    <!-- VINCULACIÓN EXPRESS -->
    <div
      v-if="props.contacto.rol === 'titular'"
      class="border border-slate-200/80 dark:border-slate-700 rounded-xl overflow-hidden bg-white dark:bg-slate-800 shadow-2xs"
    >
      <button
        @click="des_vinculacion = !des_vinculacion"
        class="w-full flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100/70 dark:hover:bg-slate-700/70 transition-colors text-left cursor-pointer"
      >
        <div class="flex items-center gap-2">
          <span
            class="text-[10px] font-black text-subtle uppercase tracking-wider"
          >
            Vinculación Express
          </span>

          <span
            class="text-[8px] font-mono bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-1.5 py-0.5 rounded font-black"
          >
            {{ totalMiembros }}/5 Cupos
          </span>
        </div>

        <span
          class="text-slate-400 dark:text-slate-500 text-[10px] transform transition-transform duration-200"
          :class="des_vinculacion ? 'rotate-180' : ''"
        >
          ▼
        </span>
      </button>

      <div
        v-show="des_vinculacion"
        class="p-2.5 border-t border-slate-100 dark:border-slate-700 max-h-60 overflow-y-auto scrollbar-thin space-y-2"
      >
        <div v-if="totalMiembros < 5" class="space-y-2">
          <div>
            <input
              type="text"
              v-model="nuevoBeneficiario.nombreCompleto"
              placeholder="Nombre Completo *"
              class="w-full bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 rounded-lg border border-slate-200 dark:border-slate-600 px-2 py-1.5 text-[11px] focus:outline-none focus:ring-1 focus:ring-blue-600 transition-all font-semibold"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <select
                v-model="nuevoBeneficiario.tipoDocumento"
                class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg p-1.5 font-semibold text-slate-700 dark:text-slate-300 outline-none text-[11px]"
              >
                <option value="CC">CC</option>
                <option value="TI">TI</option>
                <option value="RC">RC</option>
                <option value="CE">CE</option>
              </select>
            </div>

            <div>
              <input
                type="text"
                v-model="nuevoBeneficiario.documento"
                placeholder="N° Documento *"
                class="w-full bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 rounded-lg border border-slate-200 dark:border-slate-600 px-2 py-1.5 text-[11px] focus:outline-none focus:ring-1 focus:ring-blue-600 transition-all font-mono font-bold"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <input
                type="number"
                v-model="nuevoBeneficiario.edad"
                placeholder="Edad"
                min="0"
                class="w-full bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-200 rounded-lg border border-slate-200 dark:border-slate-600 px-2 py-1.5 text-[11px] font-mono font-bold"
              />
            </div>

            <div>
              <select
                v-model="nuevoBeneficiario.genero"
                class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg p-1.5 font-semibold text-slate-700 dark:text-slate-300 outline-none text-[11px]"
              >
                <option value="Masculino">Masculino</option>
                <option value="Femenino">Femenino</option>
                <option value="Otro">Otro</option>
              </select>
            </div>
          </div>

          <div>
            <select
              v-model="nuevoBeneficiario.parentesco"
              class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg p-1.5 font-semibold text-slate-700 dark:text-slate-300 outline-none text-[11px]"
            >
              <option value="Hijo(a)">Hijo(a)</option>
              <option value="Cónyuge">Cónyuge</option>
              <option value="Padre/Madre">Padre/Madre</option>
              <option value="Hermano(a)">Hermano(a)</option>
              <option value="Otro">Otro</option>
            </select>
          </div>

          <button
            @click="ejecutarVinculacion"
            class="w-full bg-blue-700 hover:bg-blue-800 text-white font-black text-[9px] py-2 px-3 uppercase tracking-wider rounded-lg cursor-pointer transition-colors text-center border border-blue-800 mt-1"
          >
            Agregar Beneficiario
          </button>
        </div>

        <div
          v-else
          class="text-[9px] text-muted italic text-center p-2 surface-sunken rounded-lg border border-dashed border-slate-200 dark:border-slate-600 font-medium"
        >
          Límite familiar alcanzado (Máximo 5 miembros).
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>

