<script setup lang="ts">
withDefaults(defineProps<{ nombre: string; size?: 'sm' | 'md' }>(), { size: 'md' })

const iniciales = (nombre: string) => nombre.split(' ').map(n => n[0]).slice(0, 2).join('')
</script>

<template>
  <div
    class="rounded-xl bg-[#EEF2FF] text-slate-900 font-bold flex items-center justify-center flex-shrink-0"
    :class="size === 'sm' ? 'w-6 h-6 !rounded-full text-[8px]' : 'w-9 h-9 text-[12px]'"
  >
    {{ iniciales(nombre) }}
  </div>
</template>
