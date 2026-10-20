<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ChevronDown, PanelLeftClose, Search } from 'lucide-vue-next'
import {
  VINCULACIONES, OPC_ULTIMO_USO,
  type FiltroSegmento,
} from '../constants/ciclo-afiliado.constants'
import { getUbicaciones, getConceptosServicios, type UbicacionApi, type ConceptoServicioApi } from '../services/segmentos.api'

const f = defineModel<FiltroSegmento>({ required: true })
const emit = defineEmits<{ aplicar: []; limpiar: []; colapsar: [] }>()

const buscarFiltro = ref('')
const buscarDepartamento = ref('')
const buscarCiudad = ref('')
const buscarConcepto = ref('')
const buscarServicio = ref('')
const nf = new Intl.NumberFormat('es-CO')

// Departamento/ciudad y concepto/servicio salen de TMPBI1 (via el backend,
// que los cachea porque esa tabla tiene millones de filas), como pares
// relacionados: primero se elige departamento/concepto, y el desplegable
// de ciudad/servicio se filtra a lo que realmente le pertenece en TMPBI1.
// Se cargan una vez al montar el panel de filtros.
const ubicaciones = ref<UbicacionApi[]>([])
const conceptosServicios = ref<ConceptoServicioApi[]>([])
const cargandoOpciones = ref(true)
const errorOpciones = ref<string | null>(null)
onMounted(async () => {
  const [u, cs] = await Promise.allSettled([getUbicaciones(), getConceptosServicios()])
  if (u.status === 'fulfilled') ubicaciones.value = u.value
  if (cs.status === 'fulfilled') conceptosServicios.value = cs.value
  // Si alguna fallo, se avisa (antes quedaba vacio en silencio y no se
  // sabia si era un bug o si faltaba reiniciar el backend).
  const fallidas = [u, cs].filter(r => r.status === 'rejected') as PromiseRejectedResult[]
  if (fallidas.length) {
    errorOpciones.value = fallidas
      .map(r => (r.reason instanceof Error ? r.reason.message : String(r.reason)))
      .join(' · ')
  }
  cargandoOpciones.value = false
})

const departamentos = computed(() => {
  const q = buscarDepartamento.value.toLowerCase().trim()
  const todos = [...new Set(ubicaciones.value.map(u => u.departamento))].sort()
  return q ? todos.filter(d => d.toLowerCase().includes(q)) : todos
})
// Municipios del departamento elegido; si no hay departamento elegido,
// todos los municipios (sin repetir, por si el mismo nombre aparece en
// mas de un departamento).
const ciudadesDisponibles = computed(() => {
  const q = buscarCiudad.value.toLowerCase().trim()
  const base = f.value.departamento
    ? ubicaciones.value.filter(u => u.departamento === f.value.departamento)
    : ubicaciones.value
  const todas = [...new Set(base.map(u => u.municipio))].sort()
  return q ? todas.filter(c => c.toLowerCase().includes(q)) : todas
})

const elegirDepartamento = (valor: string) => {
  f.value.departamento = f.value.departamento === valor ? '' : valor
  // Si la ciudad marcada no pertenece al departamento nuevo, se limpia.
  if (f.value.ciudades[0] && !ciudadesDisponibles.value.includes(f.value.ciudades[0])) {
    f.value.ciudades = []
  }
}
const elegirCiudad = (valor: string) => {
  f.value.ciudades = f.value.ciudades[0] === valor ? [] : [valor]
}

const visible = (label: string) =>
  !buscarFiltro.value || label.toLowerCase().includes(buscarFiltro.value.toLowerCase())

// Cada seccion es un desplegable: arranca abierta si ya trae un valor
// activo (para que se note de una), y las demas cerradas para que el
// panel quede compacto. Buscar en "Buscar filtro…" abre de una las que
// coincidan, para no tener que abrirlas a mano.
const expandidas = ref<Set<string>>(new Set(['plan', 'sexo']))
const toggleSeccion = (clave: string) => {
  const nueva = new Set(expandidas.value)
  nueva.has(clave) ? nueva.delete(clave) : nueva.add(clave)
  expandidas.value = nueva
}
// Al elegir "Plan Liga" se abre de una la seccion "Uso del plan" (si no, queda
// colapsada como cualquier otra seccion y hay que abrirla a mano para notar
// que existe -- se pasa por alto facil porque solo aparece con este chip).
const expandirSeccion = (clave: string) => {
  if (expandidas.value.has(clave)) return
  const nueva = new Set(expandidas.value)
  nueva.add(clave)
  expandidas.value = nueva
}
const abierta = (clave: string) => expandidas.value.has(clave) || !!buscarFiltro.value.trim()

const toggle = (arr: string[], v: string) => {
  const i = arr.indexOf(v)
  if (i >= 0) arr.splice(i, 1); else arr.push(v)
}

const conceptos = computed(() => [...new Set(conceptosServicios.value.map(p => p.concepto))].sort())
const conceptosFiltrados = computed(() => {
  const q = buscarConcepto.value.toLowerCase().trim()
  return q ? conceptos.value.filter(c => c.toLowerCase().includes(q)) : conceptos.value
})

// Servicios del/los concepto(s) marcados; si no hay ninguno marcado, todos
// los servicios (sin repetir, por si el mismo servicio aparece en mas de
// un concepto).
const serviciosDelConcepto = computed(() => {
  const base = f.value.conceptos.length
    ? conceptosServicios.value.filter(p => f.value.conceptos.includes(p.concepto))
    : conceptosServicios.value
  return [...new Set(base.map(p => p.servicio))].sort()
})
const serviciosFiltrados = computed(() => {
  const q = buscarServicio.value.toLowerCase().trim()
  const base = serviciosDelConcepto.value
  const filtrados = q ? base.filter(s => s.toLowerCase().includes(q)) : base
  // Con al menos un concepto marcado, la lista ya viene acotada (no son
  // miles) -- se muestra completa. Sin concepto, se limita a 8 para no
  // listar los 6000+ servicios de TMPBI1 de una vez.
  return f.value.conceptos.length ? filtrados : filtrados.slice(0, 8)
})
const serviciosRestantes = computed(() => serviciosDelConcepto.value.length - serviciosFiltrados.value.length)

// Botones de opción con esquinas suaves (mismo estilo que los botones de Grupos de interés).
const CHIP = 'h-7 px-2.5 text-[11px] font-semibold rounded-md border transition-colors'
const chipCls = (on: boolean) => on
  ? 'bg-[#2447F9] border-[#2447F9] text-white'
  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-600 text-body hover:border-slate-400 dark:hover:border-slate-500'
</script>

<template>
  <div class="surface-card rounded-xl shadow-sm overflow-hidden lg:sticky lg:top-3 flex flex-col lg:h-[calc(100vh-190px)]">
    <div class="px-4 py-3 border-b border-default flex items-center justify-between gap-2 shrink-0">
      <h3 class="text-[12px] font-bold text-heading">Filtros de segmento</h3>
      <div class="flex items-center gap-2">
        <button type="button" class="text-[10px] font-bold text-slate-900 hover:underline" @click="emit('limpiar')">Limpiar</button>
        <button
          type="button"
          class="hidden lg:inline-flex w-7 h-7 items-center justify-center rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-[#2447F9] transition-colors"
          title="Minimizar filtros"
          @click="emit('colapsar')"
        >
          <PanelLeftClose :size="14" />
        </button>
      </div>
    </div>

    <div class="px-4 py-3 border-b border-default shrink-0">
      <div class="relative">
        <Search :size="13" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input v-model="buscarFiltro" placeholder="Buscar filtro…" class="w-full h-8 pl-8 pr-2 rounded-lg input-surface text-[11px] outline-none" />
      </div>
    </div>

    <div class="flex-1 min-h-0 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700">
      <!-- Aviso si fallo la carga de departamentos/ciudades/conceptos/servicios -->
      <div v-if="errorOpciones" class="mx-4 mt-3 rounded-lg bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-[10px] font-semibold px-3 py-2">
        No se pudieron cargar algunas opciones de filtro: {{ errorOpciones }}
      </div>

      <!-- Plan -->
      <section v-show="visible('Plan Plan Liga')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('plan')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Plan
            <span v-if="f.planLiga" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('plan') }" />
        </button>
        <div v-show="abierta('plan')" class="px-4 pb-3">
          <div class="flex flex-wrap gap-1.5">
            <button @click="f.planLiga = ''; f.usoPlan = ''" :class="[CHIP, chipCls(f.planLiga === '')]">Todos</button>
            <button v-for="o in ['Plan Liga', 'No plan Liga']" :key="o"
              @click="f.planLiga = (f.planLiga === o ? '' : o) as FiltroSegmento['planLiga']; f.planLiga === 'Plan Liga' ? expandirSeccion('usoPlan') : (f.usoPlan = '')"
              :class="[CHIP, chipCls(f.planLiga === o)]">{{ o }}</button>
          </div>
        </div>
      </section>

      <!-- Uso del plan: solo tiene sentido con Plan Liga elegido (sale de otra
      consulta, ver segmentos.api.ts / backend). Con "Todos" o "No plan Liga"
      no se muestra, y si estaba marcado se limpia solo (ver arriba). -->
      <section v-show="f.planLiga === 'Plan Liga' && visible('Uso del plan Con uso Sin uso')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('usoPlan')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Uso del plan
            <span v-if="f.usoPlan" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('usoPlan') }" />
        </button>
        <div v-show="abierta('usoPlan')" class="px-4 pb-3">
          <div class="flex flex-wrap gap-1.5">
            <button @click="f.usoPlan = ''" :class="[CHIP, chipCls(f.usoPlan === '')]">Todos</button>
            <button @click="f.usoPlan = f.usoPlan === 'con_uso' ? '' : 'con_uso'" :class="[CHIP, chipCls(f.usoPlan === 'con_uso')]">Con uso</button>
            <button @click="f.usoPlan = f.usoPlan === 'sin_uso' ? '' : 'sin_uso'" :class="[CHIP, chipCls(f.usoPlan === 'sin_uso')]">Sin uso</button>
          </div>
          <p v-if="f.usoPlan === ''" class="text-[10px] text-muted mt-2">
            Incluye a quienes han usado el plan y a quienes no. Si además filtra por concepto, servicio o último uso, solo salen quienes lo han usado.
          </p>
          <p v-if="f.usoPlan === 'sin_uso'" class="text-[10px] text-muted mt-2">
            Activos de Plan Liga sin ningún servicio registrado. Los filtros de concepto, servicio y último uso no aplican aquí.
          </p>
        </div>
      </section>

      <!-- Sexo -->
      <section v-show="visible('Sexo')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('sexo')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Sexo
            <span v-if="f.sexo" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('sexo') }" />
        </button>
        <div v-show="abierta('sexo')" class="px-4 pb-3">
          <div class="flex gap-1.5">
            <button v-for="[v, l] in [['', 'Todos'], ['F', 'Mujeres'], ['M', 'Hombres']]" :key="v"
              @click="f.sexo = v as FiltroSegmento['sexo']" :class="[CHIP, chipCls(f.sexo === v)]">{{ l }}</button>
          </div>
        </div>
      </section>

      <!-- Rango de edad -->
      <section v-show="visible('Rango de edad')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('edad')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Rango de edad
            <span v-if="f.edadMin || f.edadMax" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('edad') }" />
        </button>
        <div v-show="abierta('edad')" class="px-4 pb-3">
          <div class="flex items-center gap-2">
            <input v-model="f.edadMin" type="number" min="0" max="120" placeholder="mín" class="w-full h-8 px-2 rounded-lg input-surface text-[11px] outline-none" />
            <span class="text-slate-400 text-[11px]">a</span>
            <input v-model="f.edadMax" type="number" min="0" max="120" placeholder="máx" class="w-full h-8 px-2 rounded-lg input-surface text-[11px] outline-none" />
          </div>
        </div>
      </section>

      <!-- Departamento -->
      <section v-show="visible('Departamento')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('departamento')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Departamento
            <span v-if="f.departamento" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('departamento') }" />
        </button>
        <div v-show="abierta('departamento')" class="px-4 pb-3">
          <div class="relative mb-2">
            <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input v-model="buscarDepartamento" placeholder="Buscar departamento…" class="w-full h-8 pl-8 pr-2 rounded-lg input-surface text-[11px] outline-none" />
          </div>
          <p v-if="cargandoOpciones" class="text-[10px] text-muted">Cargando…</p>
          <p v-else-if="!departamentos.length" class="text-[10px] text-muted">Sin resultados.</p>
          <div v-else class="max-h-40 overflow-y-auto">
            <label v-for="d in departamentos" :key="d" class="flex items-center gap-2 py-1 text-[11px] text-body cursor-pointer">
              <input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9] shrink-0" :checked="f.departamento === d" @change="elegirDepartamento(d)" />
              <span class="truncate" :title="d">{{ d }}</span>
            </label>
          </div>
        </div>
      </section>

      <!-- Ciudad / municipio -->
      <section v-show="visible('Ciudad Municipio')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('ciudad')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">
            Ciudad / municipio
            <span v-if="f.ciudades.length" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('ciudad') }" />
        </button>
        <div v-show="abierta('ciudad')" class="px-4 pb-3">
          <p v-if="f.departamento" class="text-[10px] text-muted mb-2">Municipios de {{ f.departamento }}</p>
          <div class="relative mb-2">
            <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input v-model="buscarCiudad" placeholder="Buscar ciudad…" class="w-full h-8 pl-8 pr-2 rounded-lg input-surface text-[11px] outline-none" />
          </div>
          <p v-if="cargandoOpciones" class="text-[10px] text-muted">Cargando…</p>
          <p v-else-if="!ciudadesDisponibles.length" class="text-[10px] text-muted">Sin resultados.</p>
          <div v-else class="max-h-40 overflow-y-auto">
            <label v-for="c in ciudadesDisponibles" :key="c" class="flex items-center gap-2 py-1 text-[11px] text-body cursor-pointer">
              <input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9] shrink-0" :checked="f.ciudades[0] === c" @change="elegirCiudad(c)" />
              <span class="truncate" :title="c">{{ c }}</span>
            </label>
          </div>
        </div>
      </section>

      <!-- Concepto -->
      <section v-show="visible('Concepto')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('concepto')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Concepto
            <span v-if="f.conceptos.length" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('concepto') }" />
        </button>
        <div v-show="abierta('concepto')" class="px-4 pb-3">
          <div class="relative mb-2">
            <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input v-model="buscarConcepto" placeholder="Buscar concepto…" class="w-full h-8 pl-8 pr-2 rounded-lg input-surface text-[11px] outline-none" />
          </div>
          <div class="max-h-48 overflow-y-auto">
            <label v-for="c in conceptosFiltrados" :key="c" class="flex items-center gap-2 py-1 text-[11px] text-body cursor-pointer">
              <input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9] shrink-0" :checked="f.conceptos.includes(c)" @change="toggle(f.conceptos, c)" />
              <span class="truncate" :title="c">{{ c }}</span>
            </label>
          </div>
        </div>
      </section>

      <!-- Servicio -->
      <section v-show="visible('Servicio')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('servicio')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">
            Servicio
            <span v-if="f.servicios.length" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('servicio') }" />
        </button>
        <div v-show="abierta('servicio')" class="px-4 pb-3">
          <p v-if="f.conceptos.length" class="text-[10px] text-muted mb-2 truncate">De: {{ f.conceptos.join(', ') }}</p>
          <div class="relative mb-2">
            <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input v-model="buscarServicio" placeholder="Buscar servicio…" class="w-full h-8 pl-8 pr-2 rounded-lg input-surface text-[11px] outline-none" />
          </div>
          <div class="max-h-48 overflow-y-auto">
            <label v-for="s in serviciosFiltrados" :key="s" class="flex items-center gap-2 py-1 text-[11px] text-body cursor-pointer">
              <input type="checkbox" class="w-3.5 h-3.5 accent-[#2447F9] shrink-0" :checked="f.servicios.includes(s)" @change="toggle(f.servicios, s)" />
              <span class="truncate" :title="s">{{ s }}</span>
            </label>
          </div>
          <p v-if="serviciosRestantes > 0" class="text-[10px] text-muted mt-1">+ {{ nf.format(serviciosRestantes) }} más</p>
        </div>
      </section>

      <!-- Último uso -->
      <section v-show="visible('Último uso de servicios')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('ultimoUso')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Último uso
            <span v-if="f.ultimoUso" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('ultimoUso') }" />
        </button>
        <div v-show="abierta('ultimoUso')" class="px-4 pb-3">
          <div class="flex flex-wrap gap-1.5">
            <button v-for="o in OPC_ULTIMO_USO" :key="o.v" @click="f.ultimoUso = o.v" :class="[CHIP, chipCls(f.ultimoUso === o.v)]">{{ o.l }}</button>
          </div>
        </div>
      </section>

      <!-- Tipo de vinculación -->
      <section v-show="visible('Tipo de vinculación')">
        <button type="button" class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors" @click="toggleSeccion('vinculacion')">
          <span class="text-[10px] font-bold text-subtle uppercase tracking-wide flex items-center gap-1.5">Tipo de vinculación
            <span v-if="f.vinculacion" class="w-1.5 h-1.5 rounded-sm bg-[#2447F9]"></span>
          </span>
          <ChevronDown :size="14" class="text-slate-400 transition-transform shrink-0" :class="{ 'rotate-180': abierta('vinculacion') }" />
        </button>
        <div v-show="abierta('vinculacion')" class="px-4 pb-3">
          <div class="flex flex-wrap gap-1.5">
            <button v-for="o in VINCULACIONES" :key="o" @click="f.vinculacion = f.vinculacion === o ? '' : o"
              :class="[CHIP, chipCls(f.vinculacion === o)]">{{ o }}</button>
          </div>
        </div>
      </section>
    </div>

    <div class="px-4 py-3 border-t border-default flex gap-2 shrink-0">
      <button @click="emit('limpiar')" class="flex-1 h-9 rounded-lg border border-default bg-white dark:bg-slate-800 text-[11px] font-semibold text-body hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">Limpiar</button>
      <button @click="emit('aplicar')" class="flex-1 h-9 rounded-lg bg-[#2447F9] text-white text-[11px] font-bold shadow hover:bg-[#1D3DD9] transition-all">Aplicar</button>
    </div>
  </div>
</template>

