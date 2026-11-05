import * as XLSX from 'xlsx'
import type { ModuloSeleccion, RegistroCambio } from '../types/auditoria'
import { ACCION_LABEL, MODULO_POR_KEY, ORIGEN_LABEL } from '../constants/auditoria.constants'
import { formatoFecha, formatoFechaHora, hoyISO } from './fechas'

const siNo = (v: boolean | null) => (v === null ? '' : v ? 'Sí' : 'No')
const sufijoModulo = (m: ModuloSeleccion) => (m === 'todos' ? 'todos' : m)

export function exportarCambiosExcel(cambios: RegistroCambio[], modulo: ModuloSeleccion): void {
  const filas = cambios.map(c => ({
    'Fecha y hora': formatoFechaHora(c.fecha),
    'Usuario': c.usuario.nombre,
    'Login': c.usuario.usuario,
    'ID usuario': c.usuario.id,
    'Rol': c.usuario.rol,
    'IP': c.ip,
    'Acción': ACCION_LABEL[c.accion],
    'Origen': ORIGEN_LABEL[c.origen],
    'Lote': c.loteId ?? '',
    'Módulo': MODULO_POR_KEY[c.modulo].label,
    'ID registro': c.registroId,
    'Registro': c.registroNombre,
    'Documento': c.documento,
    'Grupo (titular)': c.grupoTitular ? `${c.grupoTitular.nombre} (${c.grupoTitular.documento})` : '',
    'Estado antes': c.estadoAntes ?? '',
    'Estado después': c.estadoDespues ?? '',
    'Fecha ingreso': c.fechaIngreso ? formatoFecha(c.fechaIngreso) : '',
    'Renovado': siNo(c.renovado),
    'Fecha renovación': c.fechaRenovado ? formatoFecha(c.fechaRenovado) : '',
    'Vigencia hasta': c.vigenciaHasta ? formatoFecha(c.vigenciaHasta) : '',
    'Motivo': c.motivo,
    'Campos modificados': c.campos.map(f => `${f.etiqueta}: ${f.antes ?? '(vacío)'} → ${f.despues ?? '(vacío)'}`).join(' | '),
  }))

  const hoja = XLSX.utils.json_to_sheet(filas)
  hoja['!cols'] = [18, 24, 14, 10, 20, 14, 16, 12, 22, 14, 11, 28, 16, 30, 14, 14, 13, 10, 15, 14, 30, 60].map(wch => ({ wch }))

  const libro = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(libro, hoja, 'Cambios')
  XLSX.writeFile(libro, `auditoria_cambios_${sufijoModulo(modulo)}_${hoyISO()}.xlsx`)
}
