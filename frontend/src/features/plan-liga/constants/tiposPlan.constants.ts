// Tipos de plan (columna TIPO_PLAN de INTRANET_VISTA_PLANLIGA) que se ofrecen en el
// selector del formulario de titular. Por ahora es una lista fija tomada de los
// valores con titulares activos; el valor se guarda tal cual en TIPO_PLAN.
// (' LIGA' con espacio inicial se omite: es el mismo 'LIGA' mal digitado.)
export const TIPOS_PLAN = [
  'EEP GC',
  'MAGNETRON',
  'NUCLEO',
  'CAFE Y MODA',
  'ENERGIA',
  'FRISBY',
  'DISEÑOS',
  'CORREDORES',
  'CODEGAR',
  'EEP',
  'REFRIGERAR',
  'LIGA',
  'INTEGRIDAD',
  'CORTESIA',
  'MAXTICAFE',
  'MOVITRAM',
  'PEREIRA PLAZA',
  'CAMARA DOSQUEBRADAS',
  'SAN JOSE',
  'VOLUNTARIA',
  'MACARENA',
  'CM ESTRUCTURAS',
  'INTERANDINA',
  'CARDER',
  'SERRANO',
  'PARTICULAR',
  'MILLAN',
  'OKLA',
  'CYP',
  'Servimotos Occidente',
  'NOMA',
  'VOLUNTARIA-50',
  'CAMARA',
  'JT',
  'DISEÑOS CON ESTILO',
] as const

export type TipoPlan = (typeof TIPOS_PLAN)[number]
