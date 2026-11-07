import * as XLSX from 'xlsx'
import type { ModuloSeleccion, RegistroCambio } from '../types/auditoria'
import { ACCION_LABEL, MODULO_POR_KEY, ORIGEN_LABEL } from '../constants/auditoria.constants'
import { formatoFecha, formatoFechaHora, hoyISO } from './fechas'

const siNo = (v: boolean | null) => (v === null ? '' : v ? 'Sí' : 'No')
const sufijoModulo = (m: ModuloSeleccion) => (m === 'todos' ? 'todos' : m)

export function exportarCambiosExcel(cambios: RegistroCambio[], modulo: ModuloSeleccion): void {
  const conPlanLiga = cambios.some(c => c.modulo === 'titulares' || c.modulo === 'beneficiarios')
  const filas = cambios.map(c => {
    const fila: Record<string, string | number> = {
      'Fecha y hora': formatoFechaHora(c.fecha),
      'Usuario': c.usuario.nombre,
      'Login': c.usuario.usuario,
      'ID usuario': c.usuario.id,
      'Rol': c.usuario.rol,
      'Acción': ACCION_LABEL[c.accion],
      'Origen': ORIGEN_LABEL[c.origen],
      'Módulo': MODULO_POR_KEY[c.modulo].label,
      'ID registro': c.registroId,
      'Registro': c.registroNombre,
      'Documento': c.documento,
      'Estado antes': c.estadoAntes ?? '',
      'Estado después': c.estadoDespues ?? '',
    }
    if (conPlanLiga) {
      Object.assign(fila, {
        'ID titular': c.idTitular ?? '',
        'ID beneficiario': c.idBeneficiario ?? '',
        'Grupo (titular)': c.grupoTitular ? `${c.grupoTitular.nombre} (${c.grupoTitular.documento})` : '',
        'Fecha inscripción': c.fechaInscripcion ? formatoFecha(c.fechaInscripcion) : '',
        'Fecha registro': c.fechaRegistro ? formatoFechaHora(c.fechaRegistro) : '',
        'Fecha ingreso': c.fechaIngreso ? formatoFecha(c.fechaIngreso) : '',
        'Fin de vigencia': c.vigenciaHasta ? formatoFecha(c.vigenciaHasta) : '',
        'Renovado': siNo(c.renovado),
      })
    }
    return fila
  })

  const hoja = XLSX.utils.json_to_sheet(filas)
  const anchos = [18, 24, 14, 10, 20, 16, 12, 14, 11, 28, 16, 14, 14]
  if (conPlanLiga) anchos.push(10, 14, 30, 16, 14, 13, 14, 10)
  hoja['!cols'] = anchos.map(wch => ({ wch }))

  const libro = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(libro, hoja, 'Cambios')
  XLSX.writeFile(libro, `auditoria_cambios_${sufijoModulo(modulo)}_${hoyISO()}.xlsx`)
}
