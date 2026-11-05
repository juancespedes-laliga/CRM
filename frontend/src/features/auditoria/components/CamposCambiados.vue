<script setup lang="ts">
import { ArrowRight } from 'lucide-vue-next'
import type { CampoCambiado } from '../types/auditoria'
import { claseEstado } from '../constants/auditoria.constants'

defineProps<{ campos: CampoCambiado[]; compacto?: boolean }>()

const esFechaISO = (v: string) => /^\d{4}-\d{2}-\d{2}$/.test(v)
const mostrar = (v: string | null) => {
  if (v === null || v === '') return '(vacío)'
  if (esFechaISO(v)) return new Date(`${v}T00:00:00`).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
  return v
}
// Solo el campo Estado lleva color; el resto se ve neutro.
const claseValor = (campo: string, v: string | null) => {
  if (v === null || v === '') return 'text-muted italic'
  return campo === 'ESTADO' ? `font-semibold ${claseEstado(v)}` : 'text-body'
}
</script>

<template>
  <p v-if="campos.length === 0" class="text-[11px] text-muted">No hay campos modificados registrados.</p>
  <ul v-else class="divide-y divide-slate-100 dark:divide-slate-700" :class="compacto ? '' : 'surface-sunken rounded-xl'">
    <li v-for="c in campos" :key="c.campo" class="grid grid-cols-[110px_1fr] gap-2 text-[11px]" :class="compacto ? 'py-1' : 'px-3 py-2'">
      <span class="font-semibold text-subtle truncate" :title="c.etiqueta">{{ c.etiqueta }}</span>
      <span class="flex items-center gap-1.5 min-w-0 flex-wrap">
        <span class="break-all" :class="[claseValor(c.campo, c.antes), c.antes ? 'line-through decoration-slate-300 dark:decoration-slate-600' : '']">{{ mostrar(c.antes) }}</span>
        <ArrowRight :size="11" class="text-slate-400 dark:text-slate-500 shrink-0" />
        <span class="break-all" :class="claseValor(c.campo, c.despues)">{{ mostrar(c.despues) }}</span>
      </span>
    </li>
  </ul>
</template>
