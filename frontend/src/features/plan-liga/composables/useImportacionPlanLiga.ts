import { ref, computed, onMounted } from 'vue'
import type { AccionMasiva, PlanServicio, ResultadoImportacion, TipoImportacion } from '../types/plan-liga'
import { CUPO_MAXIMO } from '../constants/plan-liga.constants'
import { getPlanesServicio } from '../services/plan-liga.api'
import { conOrigenAuditoria } from '@/features/auth/composables/useAuth'
import { useUbicaciones, esperarUbicaciones } from '@/shared/composables/useUbicaciones'
import { agruparFilas, parsearArchivoCargaMasiva, procesarCargaMasiva, validarGruposCargaMasiva } from '../utils/cargaMasiva'
import { parsearArchivoAccionTitulares, procesarAccionMasivaTitulares, validarFilasAccionTitulares } from '../utils/accionMasivaTitulares'
import { parsearArchivoAccionBeneficiarios, procesarAccionMasivaBeneficiarios, validarFilasAccionBeneficiarios } from '../utils/accionMasivaBeneficiarios'

export function useImportacionPlanLiga() {
  const tipoImport       = ref<TipoImportacion>('agregar_grupos')
  const accionMasiva     = ref<AccionMasiva>('activar')
  const archivoNombre    = ref('')
  const archivo          = ref<File | null>(null)
  const procesandoImport = ref(false)
  const resultadoImport  = ref<ResultadoImportacion | null>(null)
  const dragOverImport   = ref(false)
  const progresoImport   = ref({ hechos: 0, total: 0 })

  // Los 3 tipos de importación ya están conectados al backend. "agregar_grupos" necesita saber
  // el cupo de beneficiarios del plan elegido para agrupar filas.
  const planesServicio = ref<PlanServicio[]>([])
  const planSeleccionado = ref<number | 'estandar'>('estandar')
  const { departamentos, municipios } = useUbicaciones()
  const cupoBeneficiarios = computed(() => {
    if (planSeleccionado.value === 'estandar') return CUPO_MAXIMO
    return planesServicio.value.find(p => p.id === planSeleccionado.value)?.cupoBeneficiarios ?? CUPO_MAXIMO
  })

  onMounted(async () => {
    try {
      planesServicio.value = await getPlanesServicio()
    } catch {
      planesServicio.value = []
    }
  })

  const seleccionarTipo = (tipo: TipoImportacion) => {
    tipoImport.value = tipo
    resetImport()
  }

  const guardarArchivo = (file: File) => {
    archivo.value = file
    archivoNombre.value = file.name
  }

  const onDragOverImport  = (e: DragEvent) => { e.preventDefault(); dragOverImport.value = true }
  const onDragLeaveImport = () => { dragOverImport.value = false }
  const onDropImport = (e: DragEvent) => {
    e.preventDefault(); dragOverImport.value = false
    const file = e.dataTransfer?.files[0]
    if (file) guardarArchivo(file)
  }
  const onFileInput = (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) guardarArchivo(file)
  }

  const procesarImport = async () => {
    if (!archivo.value) return

    procesandoImport.value = true
    resultadoImport.value = null
    progresoImport.value = { hechos: 0, total: 0 }
    try {
      if (tipoImport.value === 'titular') {
        const filas = await parsearArchivoAccionTitulares(archivo.value)
        const erroresFormato = validarFilasAccionTitulares(filas, accionMasiva.value)
        if (erroresFormato.length > 0) {
          resultadoImport.value = { total: filas.length, exitosos: 0, errores: erroresFormato.length, detalleErrores: erroresFormato, bloqueado: true }
          return
        }
        resultadoImport.value = await conOrigenAuditoria('excel', archivoNombre.value, () => procesarAccionMasivaTitulares(
          filas,
          accionMasiva.value,
          (hechos, total) => { progresoImport.value = { hechos, total } },
        ))
      } else if (tipoImport.value === 'beneficiario') {
        const filas = await parsearArchivoAccionBeneficiarios(archivo.value)
        const erroresFormato = validarFilasAccionBeneficiarios(filas, accionMasiva.value)
        if (erroresFormato.length > 0) {
          resultadoImport.value = { total: filas.length, exitosos: 0, errores: erroresFormato.length, detalleErrores: erroresFormato, bloqueado: true }
          return
        }
        resultadoImport.value = await conOrigenAuditoria('excel', archivoNombre.value, () => procesarAccionMasivaBeneficiarios(
          filas,
          accionMasiva.value,
          (hechos, total) => { progresoImport.value = { hechos, total } },
        ))
      } else {
        await esperarUbicaciones()
        const filas = await parsearArchivoCargaMasiva(archivo.value, { departamentos: departamentos.value, municipios: municipios.value })
        const tipoPlanId = planSeleccionado.value === 'estandar' ? null : planSeleccionado.value
        const grupos = agruparFilas(filas, cupoBeneficiarios.value).filter(g => !g.titular.vacia)
        const erroresFormato = validarGruposCargaMasiva(grupos)
        if (erroresFormato.length > 0) {
          const totalReal = grupos.reduce((sum, g) => sum + 1 + g.beneficiarios.filter(b => !b.vacia).length, 0)
          resultadoImport.value = { total: totalReal, exitosos: 0, errores: erroresFormato.length, detalleErrores: erroresFormato, bloqueado: true }
          return
        }
        resultadoImport.value = await conOrigenAuditoria('excel', archivoNombre.value, () => procesarCargaMasiva(
          filas,
          { tipoPlanId, cupoBeneficiarios: cupoBeneficiarios.value },
          (hechos, total) => { progresoImport.value = { hechos, total } },
        ))
      }
    } catch (e) {
      resultadoImport.value = {
        total: 0, exitosos: 0, errores: 1,
        detalleErrores: [e instanceof Error ? e.message : 'No se pudo procesar el archivo.'],
      }
    } finally {
      procesandoImport.value = false
    }
  }

  const resetImport = () => {
    archivoNombre.value = ''
    archivo.value = null
    resultadoImport.value = null
    progresoImport.value = { hechos: 0, total: 0 }
  }

  // Las 3 plantillas viven en frontend/public/plantillas/.
  const NOMBRES_PLANTILLA: Record<TipoImportacion, string> = {
    agregar_grupos: 'Plantilla_Carga_PlanLiga.xlsx',
    titular: 'titular.xlsx',
    beneficiario: 'beneficiario.xlsx',
  }
  const descargarPlantilla = () => {
    const nombre = NOMBRES_PLANTILLA[tipoImport.value]
    const enlace = document.createElement('a')
    enlace.href = `/plantillas/${nombre}`
    enlace.download = nombre
    enlace.click()
  }

  return {
    tipoImport, accionMasiva, archivoNombre, procesandoImport, resultadoImport, dragOverImport, progresoImport,
    planesServicio, planSeleccionado, cupoBeneficiarios,
    seleccionarTipo, onDragOverImport, onDragLeaveImport, onDropImport, onFileInput,
    procesarImport, resetImport, descargarPlantilla,
  }
}
