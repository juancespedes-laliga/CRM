/**
 * Clave para comparar nombres de categoría: sin tildes, en minúsculas y con espacios simples.
 * Así "Donante Recurrente", "donante recurrente" y " Donante  Recurrente " son la misma
 * categoría y la carga no crea duplicados (el backend debe guardar esta misma clave en una
 * columna con UNIQUE (grupo_id, nombre_normalizado)).
 */
export function normalizarNombre(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim()
}

/** Nombre "limpio" para mostrar/guardar: espacios simples y primera letra en mayúscula. */
export function limpiarNombre(texto: string): string {
  const t = texto.replace(/\s+/g, ' ').trim()
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : t
}
