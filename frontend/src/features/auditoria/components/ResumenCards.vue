<script setup lang="ts">
import type { TarjetaResumen } from '../types/auditoria'

defineProps<{
  tarjetas: TarjetaResumen[]
  /** Si se pasa, las tarjetas son clicables y la activa queda resaltada. */
  activa?: string | null
  clicables?: boolean
}>()
const emit = defineEmits<{ seleccionar: [key: string] }>()
</script>

<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 gap-3" :class="tarjetas.length >= 5 ? 'lg:grid-cols-5' : 'lg:grid-cols-4'">
    <component
      :is="clicables ? 'button' : 'div'"
      v-for="t in tarjetas"
      :key="t.key"
      :type="clicables ? 'button' : undefined"
      :aria-pressed="clicables ? activa === t.key : undefined"
      @click="clicables && emit('seleccionar', t.key)"
      class="surface-card rounded-2xl shadow-sm px-4 py-3 text-left transition-all"
      :class="[
        clicables ? 'surface-hover cursor-pointer' : '',
        activa === t.key ? 'ring-2 ring-[#2447F9] border-transparent' : '',
      ]"
    >
      <div class="flex items-center justify-between gap-2">
        <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider truncate">{{ t.label }}</span>
        <component :is="t.icono" :size="14" class="text-slate-400 dark:text-slate-500 shrink-0" />
      </div>
      <p class="mt-1 text-[22px] font-bold leading-tight tabular-nums" :class="t.claseValor ?? 'text-heading'">{{ t.valor.toLocaleString('es-CO') }}</p>
      <p v-if="t.ayuda" class="text-[10px] text-muted mt-0.5 truncate">{{ t.ayuda }}</p>
    </component>
  </div>
</template>
