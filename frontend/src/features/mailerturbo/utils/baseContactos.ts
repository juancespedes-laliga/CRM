import * as XLSX from 'xlsx'
import type { ContactoMT } from '../types/mailerturbo'
import { esCorreoValido } from '@/features/campanas/constants/campanas.constants'

// Encabezados aceptados por columna (sin tildes, en mayúscula). Así sirve tanto
// la plantilla que se descarga aquí como un Excel exportado de otro lado.
const ALIAS: Record<keyof ContactoMT, string[]> = {
  nombre: ['NOMBRE', 'NOMBRES', 'NOMBRE COMPLETO', 'NOMBRECONTACTO', 'NAME'],
  apellido: ['APELLIDO', 'APELLIDOS', 'APELLIDOCONTACTO'],
  correo: ['CORREO', 'EMAIL', 'E-MAIL', 'CORREO ELECTRONICO', 'MAIL'],
  telefono: ['TELEFONO', 'CELULAR', 'MOVIL', 'TELEFONOCONTACTO', 'WHATSAPP'],
  documento: ['DOCUMENTO', 'IDENTIFICACION', 'CEDULA', 'CC', 'NUMERO DOCUMENTO'],
  ciudad: ['CIUDAD', 'MUNICIPIO'],
}

const MAX_FILAS_BUSQUEDA_ENCABEZADO = 20

const normalizar = (s: unknown) =>
  String(s ?? '').trim().toUpperCase().normalize('NFD').replace(/[̀-ͯ]/g, '')

export interface LecturaBaseContactos {
  validos: ContactoMT[]
  /** Filas sin correo o con correo inválido (fila de Excel + motivo). */
  descartados: { fila: number; motivo: string }[]
  /** Correos repetidos dentro del mismo archivo (se deja solo la primera aparición). */
  duplicados: number
  sinTelefono: number
}

/** Lee la primera hoja de un .xlsx/.xls/.csv y la convierte en contactos para MailerTurbo. */
export async function leerBaseContactos(file: File): Promise<LecturaBaseContactos> {
  const libro = XLSX.read(await file.arrayBuffer(), { type: 'array' })
  const hoja = libro.Sheets[libro.SheetNames[0]]
  const filas = XLSX.utils.sheet_to_json<unknown[]>(hoja, { header: 1, raw: false, defval: '' })

  // La fila de encabezados es la primera (de las 20 iniciales) que tenga una columna de correo.
  let idxEnc = -1
  for (let i = 0; i < Math.min(filas.length, MAX_FILAS_BUSQUEDA_ENCABEZADO); i++) {
    if ((filas[i] ?? []).some(c => ALIAS.correo.includes(normalizar(c)))) { idxEnc = i; break }
  }
  if (idxEnc === -1) {
    throw new Error('No se encontró una columna de correo (CORREO o EMAIL). Use la plantilla de ejemplo.')
  }

  const encabezados = filas[idxEnc].map(normalizar)
  const columna = (campo: keyof ContactoMT) => encabezados.findIndex(h => ALIAS[campo].includes(h))
  const col = {
    nombre: columna('nombre'), apellido: columna('apellido'), correo: columna('correo'),
    telefono: columna('telefono'), documento: columna('documento'), ciudad: columna('ciudad'),
  }
  const valor = (fila: unknown[], idx: number) => (idx === -1 ? '' : String(fila[idx] ?? '').trim())

  const resultado: LecturaBaseContactos = { validos: [], descartados: [], duplicados: 0, sinTelefono: 0 }
  const vistos = new Set<string>()

  for (let i = idxEnc + 1; i < filas.length; i++) {
    const fila = filas[i] ?? []
    if (fila.every(c => String(c ?? '').trim() === '')) continue

    const correo = valor(fila, col.correo).toLowerCase()
    if (!correo) { resultado.descartados.push({ fila: i + 1, motivo: 'Sin correo' }); continue }
    if (!esCorreoValido(correo)) { resultado.descartados.push({ fila: i + 1, motivo: `Correo inválido: ${correo}` }); continue }
    if (vistos.has(correo)) { resultado.duplicados++; continue }
    vistos.add(correo)

    const telefono = valor(fila, col.telefono).replace(/\D/g, '')
    if (!telefono) resultado.sinTelefono++

    resultado.validos.push({
      nombre: valor(fila, col.nombre) || correo.split('@')[0],
      apellido: valor(fila, col.apellido),
      correo,
      telefono,
      documento: valor(fila, col.documento) || undefined,
      ciudad: valor(fila, col.ciudad) || undefined,
    })
  }
  return resultado
}

/** Descarga un Excel de ejemplo con las columnas que entiende leerBaseContactos. */
export function descargarPlantillaBaseContactos() {
  const hoja = XLSX.utils.aoa_to_sheet([
    ['NOMBRE', 'APELLIDO', 'CORREO', 'TELEFONO', 'DOCUMENTO', 'CIUDAD'],
    ['María', 'Gómez', 'maria.gomez@correo.com', '3001234567', '1088000000', 'Pereira'],
  ])
  hoja['!cols'] = [{ wch: 18 }, { wch: 18 }, { wch: 30 }, { wch: 14 }, { wch: 14 }, { wch: 14 }]
  const libro = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(libro, hoja, 'Contactos')
  XLSX.writeFile(libro, 'Plantilla_Contactos_MailerTurbo.xlsx')
}
