// Estadística descriptiva e inferencial básica para las métricas de campañas.
// Todas las funciones son puras y aceptan arreglos sin ordenar.

export const media = (xs: number[]) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : NaN)

/** Desviación estándar muestral (n - 1). */
export function desviacion(xs: number[]) {
  if (xs.length < 2) return NaN
  const m = media(xs)
  return Math.sqrt(xs.reduce((s, x) => s + (x - m) ** 2, 0) / (xs.length - 1))
}

/** Cuantil con interpolación lineal (tipo 7, el de Excel PERCENTIL.INC y R por defecto). */
export function cuantil(xs: number[], p: number) {
  if (!xs.length) return NaN
  const o = [...xs].sort((a, b) => a - b)
  const h = (o.length - 1) * p
  const i = Math.floor(h)
  return o[i] + (h - i) * ((o[i + 1] ?? o[i]) - o[i])
}

/** Coeficiente de asimetría muestral ajustado (G1, el de Excel COEFICIENTE.ASIMETRIA). */
export function asimetria(xs: number[]) {
  const n = xs.length
  if (n < 3) return NaN
  const m = media(xs), s = desviacion(xs)
  if (!s) return 0
  const suma = xs.reduce((a, x) => a + ((x - m) / s) ** 3, 0)
  return (n / ((n - 1) * (n - 2))) * suma
}

/** Curtosis en exceso muestral (G2, el de Excel CURTOSIS): 0 = como la normal. */
export function curtosis(xs: number[]) {
  const n = xs.length
  if (n < 4) return NaN
  const m = media(xs), s = desviacion(xs)
  if (!s) return 0
  const suma = xs.reduce((a, x) => a + ((x - m) / s) ** 4, 0)
  return (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * suma - (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))
}

export interface Resumen5 {
  n: number
  min: number
  q1: number
  mediana: number
  q3: number
  max: number
  iqr: number
  /** Bigotes de Tukey: el dato más extremo dentro de 1,5 × IQR. */
  bigoteInf: number
  bigoteSup: number
  media: number
  desviacion: number
  /** Coeficiente de variación (desviación / media), en %. */
  cv: number
  asimetria: number
  curtosis: number
}

export function resumen(xs: number[]): Resumen5 | null {
  if (!xs.length) return null
  const o = [...xs].sort((a, b) => a - b)
  const q1 = cuantil(o, 0.25), q3 = cuantil(o, 0.75), iqr = q3 - q1
  const limInf = q1 - 1.5 * iqr, limSup = q3 + 1.5 * iqr
  const m = media(o), s = desviacion(o)
  return {
    n: o.length,
    min: o[0],
    q1,
    mediana: cuantil(o, 0.5),
    q3,
    max: o[o.length - 1],
    iqr,
    bigoteInf: o.find(x => x >= limInf) ?? o[0],
    bigoteSup: [...o].reverse().find(x => x <= limSup) ?? o[o.length - 1],
    media: m,
    desviacion: s,
    cv: m ? (s / m) * 100 : NaN,
    asimetria: asimetria(o),
    curtosis: curtosis(o),
  }
}

export const esAtipico = (x: number, r: Resumen5) => x < r.q1 - 1.5 * r.iqr || x > r.q3 + 1.5 * r.iqr

/** Intervalos del histograma por la regla de Sturges, con límites "redondos". */
export function intervalos(xs: number[]): { desde: number; hasta: number }[] {
  if (!xs.length) return []
  const min = Math.min(...xs), max = Math.max(...xs)
  if (min === max) return [{ desde: min - 0.5, hasta: max + 0.5 }]
  const k = Math.ceil(Math.log2(xs.length)) + 1
  const crudo = (max - min) / k
  const mag = Math.pow(10, Math.floor(Math.log10(crudo)))
  // El ancho "redondo" más cercano (en escala logarítmica) al de Sturges.
  const ancho = [1, 2, 2.5, 5, 10].map(f => f * mag).reduce((a, b) => (Math.abs(Math.log(b / crudo)) < Math.abs(Math.log(a / crudo)) ? b : a))
  const inicio = Math.floor(min / ancho) * ancho
  const r: { desde: number; hasta: number }[] = []
  for (let d = inicio; d <= max; d += ancho) r.push({ desde: +d.toFixed(10), hasta: +(d + ancho).toFixed(10) })
  return r
}

/** Densidad de la normal N(m, s²). */
export const normalPdf = (x: number, m: number, s: number) =>
  Math.exp(-0.5 * ((x - m) / s) ** 2) / (s * Math.sqrt(2 * Math.PI))

/** Función de error (Abramowitz y Stegun 7.1.26, error < 1,5e-7). */
function erf(x: number) {
  const t = 1 / (1 + 0.3275911 * Math.abs(x))
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x)
  return x >= 0 ? y : -y
}
export const normalCdf = (z: number) => 0.5 * (1 + erf(z / Math.SQRT2))

/** Intervalo de confianza de Wilson al 95% para una proporción x/n, en %. */
export function wilson(x: number, n: number, z = 1.96): { inf: number; sup: number } | null {
  if (!n) return null
  const p = Math.min(1, Math.max(0, x / n))
  const den = 1 + (z * z) / n
  const centro = (p + (z * z) / (2 * n)) / den
  const margen = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / den
  return { inf: Math.max(0, centro - margen) * 100, sup: Math.min(1, centro + margen) * 100 }
}

export interface PruebaProporciones {
  /** Diferencia A - B en puntos porcentuales. */
  diferencia: number
  z: number
  p: number
  significativa: boolean
}

/** Prueba z de dos proporciones (bilateral, α = 0,05). */
export function pruebaProporciones(x1: number, n1: number, x2: number, n2: number): PruebaProporciones | null {
  if (!n1 || !n2) return null
  const p1 = x1 / n1, p2 = x2 / n2
  const pc = (x1 + x2) / (n1 + n2)
  const se = Math.sqrt(pc * (1 - pc) * (1 / n1 + 1 / n2))
  if (!se) return { diferencia: (p1 - p2) * 100, z: 0, p: 1, significativa: false }
  const z = (p1 - p2) / se
  const p = 2 * (1 - normalCdf(Math.abs(z)))
  return { diferencia: (p1 - p2) * 100, z, p, significativa: p < 0.05 }
}

const nf1 = (v: number, dec = 1) => v.toLocaleString('es-CO', { maximumFractionDigits: dec, minimumFractionDigits: 0 })

/** Texto corto con el resultado de la prueba, para mostrar al usuario. */
export function textoPrueba(r: PruebaProporciones | null): string {
  if (!r) return 'Sin datos suficientes para comparar.'
  const p = r.p < 0.001 ? 'p < 0,001' : `p = ${nf1(r.p, 3)}`
  return r.significativa
    ? `Diferencia estadísticamente significativa (${p}).`
    : `No significativa (${p}): la diferencia puede deberse al azar.`
}

/** Lectura en palabras de la forma de la distribución. */
export function interpretarForma(r: Resumen5): string {
  if (r.n < 8) return `Solo hay ${r.n} datos: la forma de la distribución todavía no es confiable.`
  const partes: string[] = []
  const g1 = r.asimetria, g2 = r.curtosis
  if (Math.abs(g1) < 0.5) partes.push('es aproximadamente simétrica')
  else if (g1 > 0) partes.push(`tiene sesgo a la derecha (asimetría ${nf1(g1, 2)}): la mayoría queda por debajo del promedio y unas pocas campañas suben mucho la media`)
  else partes.push(`tiene sesgo a la izquierda (asimetría ${nf1(g1, 2)}): la mayoría queda por encima del promedio y unas pocas lo bajan`)
  if (g2 > 1) partes.push(`colas pesadas (curtosis ${nf1(g2, 2)}): hay más valores extremos que en una normal`)
  else if (g2 < -1) partes.push(`es más plana que la normal (curtosis ${nf1(g2, 2)})`)
  const normal = Math.abs(g1) < 0.5 && Math.abs(g2) < 1
  return `La distribución ${partes.join(' y ')}. ${normal ? 'Se parece a una campana de Gauss, así que la media y la desviación la describen bien.' : 'No se parece a una campana de Gauss: para describirla es mejor la mediana y el rango intercuartílico que la media.'}`
}
