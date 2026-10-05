<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Mail, Phone, MapPin, UserMinus, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { CategoriaGrupo, MiembroGrupo } from '../types/grupo'

const props = defineProps<{
  rows: MiembroGrupo[]
  categorias: CategoriaGrupo[]
  puedeGestionar: boolean
}>()
const emit = defineEmits<{
  'cambiar-categoria': [miembroId: number, categoriaId: number | null]
  quitar: [miembro: MiembroGrupo]
}>()

const POR_PAGINA = 8
const pagina = ref(1)
const totalPaginas = computed(() => Math.max(1, Math.ceil(props.rows.length / POR_PAGINA)))
const visibles = computed(() => props.rows.slice((pagina.value - 1) * POR_PAGINA, pagina.value * POR_PAGINA))
watch(() => props.rows.length, () => { pagina.value = 1 })

const iniciales = (n: string) => n.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase()
const fecha = (iso: string) => iso.split('-').reverse().join('/')
const onCambio = (m: MiembroGrupo, e: Event) => {
  const v = (e.target as HTMLSelectElement).value
  emit('cambiar-categoria', m.id, v === '' ? null : Number(v))
}
</script>

<template>
  <div class="surface-card rounded-lg border border-default shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-default">
            <th class="px-4 py-3 text-[10px] font-bold text-muted uppercase tracking-wider">Persona</th>
            <th class="px-4 py-3 text-[10px] font-bold text-muted uppercase tracking-wider">Documento</th>
            <th class="px-4 py-3 text-[10px] font-bold text-muted uppercase tracking-wider">Contacto</th>
            <th class="px-4 py-3 text-[10px] font-bold text-muted uppercase tracking-wider">Ciudad</th>
            <th class="px-4 py-3 text-[10px] font-bold text-muted uppercase tracking-wider">Categoría</th>
            <th class="px-4 py-3 text-[10px] font-bold text-muted uppercase tracking-wider">Ingreso</th>
            <th v-if="puedeGestionar" class="px-4 py-3 text-[10px] font-bold text-muted uppercase tracking-wider text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in visibles" :key="m.id" class="border-b border-default last:border-0 surface-hover transition-colors">
            <td class="px-4 py-3">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-[#EEF2FF] dark:bg-blue-950/40 text-[#2447F9] dark:text-blue-300 text-[10px] font-bold flex items-center justify-center shrink-0">{{ iniciales(m.nombre) }}</div>
                <span class="text-[12px] font-semibold text-heading">{{ m.nombre }}</span>
              </div>
            </td>
            <td class="px-4 py-3 text-[11px] text-body tabular-nums"><span class="text-muted">{{ m.tipoDocumento }}</span> {{ m.documento }}</td>
            <td class="px-4 py-3">
              <div v-if="m.correo" class="flex items-center gap-1 text-[11px] text-body"><Mail :size="11" class="text-muted" />{{ m.correo }}</div>
              <div v-if="m.telefono" class="flex items-center gap-1 text-[11px] text-subtle mt-0.5"><Phone :size="11" class="text-muted" />{{ m.telefono }}</div>
            </td>
            <td class="px-4 py-3 text-[11px] text-body"><span class="flex items-center gap-1"><MapPin :size="11" class="text-muted" />{{ m.ciudad || '—' }}</span></td>
            <td class="px-4 py-3">
              <select v-if="puedeGestionar" :value="m.categoriaId ?? ''" @change="onCambio(m, $event)"
                class="h-8 px-2 rounded-lg input-surface text-[11px] font-medium text-body outline-none cursor-pointer max-w-[170px]">
                <option value="">Sin categoría</option>
                <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nombre }}</option>
              </select>
              <span v-else class="text-[11px] text-body">{{ categorias.find((c) => c.id === m.categoriaId)?.nombre ?? 'Sin categoría' }}</span>
            </td>
            <td class="px-4 py-3 text-[11px] text-subtle tabular-nums">{{ fecha(m.fechaIngreso) }}</td>
            <td v-if="puedeGestionar" class="px-4 py-3 text-right">
              <button @click="emit('quitar', m)" title="Quitar del grupo"
                class="w-8 h-8 rounded-lg inline-flex items-center justify-center text-muted hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40 transition-all">
                <UserMinus :size="14" />
              </button>
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td :colspan="puedeGestionar ? 7 : 6" class="px-4 py-10 text-center text-[12px] text-muted">No hay miembros con estos filtros.</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="totalPaginas > 1" class="flex items-center justify-end gap-2 px-4 py-3 border-t border-default">
      <button @click="pagina--" :disabled="pagina <= 1" title="Página anterior"
        class="w-8 h-8 rounded-lg border-default surface-card flex items-center justify-center text-body disabled:opacity-40"><ChevronLeft :size="14" /></button>
      <span class="text-[11px] text-muted">Página <strong class="text-body">{{ pagina }}</strong> de <strong class="text-body">{{ totalPaginas }}</strong></span>
      <button @click="pagina++" :disabled="pagina >= totalPaginas" title="Página siguiente"
        class="w-8 h-8 rounded-lg border-default surface-card flex items-center justify-center text-body disabled:opacity-40"><ChevronRight :size="14" /></button>
    </div>
  </div>
</template>
