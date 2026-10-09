<script setup lang="ts">
import { computed } from 'vue'
import { Target, Trash2, Pencil, AlarmClock, Check } from 'lucide-vue-next'
import type { Actividad } from '../types/actividad'
import { TIPO_META } from '../constants/relacionamiento.constants'
import type { Oportunidad } from '@/features/oportunidades/types/oportunidad'
import { clienteLabel } from '@/features/oportunidades/constants/oportunidades.constants'
import { permisosDeModulo } from '@/features/auth/composables/useAuth'

const { gestionar: puedeGestionar, eliminar: puedeEliminar } = permisosDeModulo('bitacora')

// `oportunidades` viaja por prop (cargada una sola vez en la página List.vue) en vez de
// pedirla acá: este componente se repite una vez por actividad, así que hacerlo local
// dispararía un fetch duplicado por cada fila del timeline.
const props = defineProps<{ actividad: Actividad; oportunidades: Oportunidad[] }>()
const emit = defineEmits<{ eliminar: []; editar: [] }>()

const oportunidad = computed(() => props.oportunidades.find(o => o.id === props.actividad.oportunidadId) ?? null)

const sujetos = computed(() => [props.actividad.contactoNombre, props.actividad.empresaNombre, props.actividad.titularNombre].filter(Boolean))

// Vencido: la fecha límite del próximo paso ya pasó. Hoy: vence hoy mismo. El resto no
// resalta (aún hay margen), solo se distingue vencido/hoy porque son los que requieren acción.
// completarActividad() ya no borra proximoPaso al completar (solo cambia "estado"), así que
// un próximo paso ya realizado sigue teniendo texto: se distingue por estado, no por presencia.
const hoy = new Date().toISOString().split('T')[0]
const estadoProximoPaso = computed<'vencido' | 'hoy' | 'proximo' | 'realizado' | null>(() => {
  if (!props.actividad.proximoPaso) return null
  if (props.actividad.estado === 'realizado') return 'realizado'
  if (!props.actividad.proximoPasoFecha) return 'proximo'
  if (props.actividad.proximoPasoFecha < hoy) return 'vencido'
  if (props.actividad.proximoPasoFecha === hoy) return 'hoy'
  return 'proximo'
})
</script>

<template>
  <div class="surface-card rounded-2xl shadow-sm p-2.5 flex gap-3 hover:shadow-md transition-all group">
    <div class="flex-shrink-0">
      <div class="w-8 h-8 rounded-xl flex items-center justify-center" :style="{ backgroundColor: TIPO_META[actividad.tipo].bg }">
        <component :is="TIPO_META[actividad.tipo].icono" :size="14" :style="{ color: TIPO_META[actividad.tipo].color }" />
      </div>
    </div>

    <div class="flex-1 min-w-0">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[10px] font-bold uppercase tracking-wide" :style="{ color: TIPO_META[actividad.tipo].color }">{{ actividad.tipo }}</span>
          <template v-for="(s, i) in sujetos" :key="i">
            <span class="text-[11px] text-muted">·</span>
            <span :class="i === 0 ? 'text-[12px] font-bold text-heading' : 'text-[11px] text-subtle'">{{ s }}</span>
          </template>
          <span v-if="sujetos.length === 0" class="text-[11px] text-muted italic">Sin contacto, empresa o titular asociado</span>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <span class="text-[10px] text-muted">{{ actividad.fecha }}</span>
          <div class="flex items-center gap-1">
            <div class="w-5 h-5 rounded-full bg-[#EEF2FF] dark:bg-blue-950/50 text-slate-900 dark:text-white text-[7px] font-bold flex items-center justify-center">
              {{ actividad.usuario.split(' ').map(n => n[0]).join('') }}
            </div>
            <span class="text-[10px] text-muted">{{ actividad.usuario }}</span>
          </div>
          <span class="w-px h-5 bg-slate-200 dark:bg-slate-700 shrink-0" />
          <button v-if="puedeGestionar" @click="emit('editar')"
            class="w-7 h-7 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:bg-blue-50 dark:hover:bg-blue-950/40 hover:border-blue-200 dark:hover:border-blue-800 hover:text-[#2447F9] dark:hover:text-blue-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-colors shrink-0"
            title="Editar actividad">
            <Pencil :size="12" />
          </button>
          <button v-if="puedeEliminar" @click="emit('eliminar')"
            class="w-7 h-7 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:bg-red-50 dark:hover:bg-red-950/40 hover:border-red-200 dark:hover:border-red-800 hover:text-red-500 dark:hover:text-red-400 text-slate-500 dark:text-slate-400 flex items-center justify-center transition-colors shrink-0"
            title="Eliminar actividad">
            <Trash2 :size="13" />
          </button>
        </div>
      </div>

      <p class="text-[12px] text-slate-700 dark:text-slate-300 mb-1 truncate">{{ actividad.accion }}</p>

      <p v-if="actividad.usuarioActualizacion" class="text-[10px] text-muted italic mb-1">
        Editado por <strong class="not-italic">{{ actividad.usuarioActualizacion }}</strong>
        <template v-if="actividad.fechaActualizacion"> · {{ actividad.fechaActualizacion }}</template>
      </p>

      <div v-if="oportunidad" class="flex items-center gap-1.5 mb-1">
        <Target :size="11" class="text-[#2447F9] dark:text-blue-400 flex-shrink-0" />
        <span class="text-[11px] text-slate-900 dark:text-white font-bold">{{ oportunidad.servicio }}</span>
        <span class="text-[10px] text-muted">· {{ clienteLabel(oportunidad) }}</span>
      </div>

      <div v-if="actividad.proximoPaso" class="flex items-center gap-2 rounded-lg px-2.5 py-1"
        :class="estadoProximoPaso === 'vencido' ? 'bg-red-50 dark:bg-red-950/40' : estadoProximoPaso === 'hoy' ? 'bg-amber-50 dark:bg-amber-950/40' : estadoProximoPaso === 'realizado' ? 'bg-emerald-50 dark:bg-emerald-950/40' : 'surface-sunken'">
        <AlarmClock v-if="estadoProximoPaso === 'vencido' || estadoProximoPaso === 'hoy'" :size="12"
          :class="estadoProximoPaso === 'vencido' ? 'text-red-500 dark:text-red-400' : 'text-amber-500 dark:text-amber-400'" class="flex-shrink-0" />
        <Check v-if="estadoProximoPaso === 'realizado'" :size="12" class="text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
        <span class="text-[9px] font-bold uppercase tracking-wide flex-shrink-0"
          :class="estadoProximoPaso === 'vencido' ? 'text-red-500 dark:text-red-400' : estadoProximoPaso === 'hoy' ? 'text-amber-600 dark:text-amber-400' : estadoProximoPaso === 'realizado' ? 'text-emerald-600 dark:text-emerald-400' : 'text-muted'">
          {{ estadoProximoPaso === 'realizado' ? 'Próx. paso realizado:' : 'Próx. paso:' }}
        </span>
        <span class="text-[11px] font-medium truncate"
          :class="estadoProximoPaso === 'vencido' ? 'text-red-600 dark:text-red-400' : estadoProximoPaso === 'hoy' ? 'text-amber-700 dark:text-amber-400' : estadoProximoPaso === 'realizado' ? 'text-emerald-700 dark:text-emerald-400 line-through' : 'text-slate-900 font-bold dark:text-white'">{{ actividad.proximoPaso }}</span>
        <span v-if="actividad.proximoPasoFecha && estadoProximoPaso !== 'realizado'" class="text-[10px] text-muted ml-auto flex-shrink-0">
          {{ estadoProximoPaso === 'vencido' ? 'Venció' : 'Para' }} {{ actividad.proximoPasoFecha }}
        </span>
      </div>
    </div>
  </div>
</template>
