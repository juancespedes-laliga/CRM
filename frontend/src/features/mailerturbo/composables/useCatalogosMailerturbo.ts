import { ref } from 'vue'
import type { ListaMT, PerfilEnvioMT, PlantillaMT } from '../types/mailerturbo'
import { crearLista, getListas, getPerfilesEnvio, getPlantillasMT } from '../services/mailerturbo.api'

// Estado a nivel de módulo: listas, plantillas y perfiles cambian poco, así que se
// comparten entre la página de MailerTurbo y los diálogos (Audiencias, Campañas)
// y solo se piden una vez por sesión (o al pulsar "Actualizar").
const listas = ref<ListaMT[]>([])
const plantillas = ref<PlantillaMT[]>([])
const perfiles = ref<PerfilEnvioMT[]>([])
const cargando = ref(false)
const error = ref<string | null>(null)
let cargado = false

export function useCatalogosMailerturbo() {
  const cargar = async (forzar = false) => {
    if ((cargado && !forzar) || cargando.value) return
    cargando.value = true
    error.value = null
    try {
      const [l, p, pe] = await Promise.all([getListas(), getPlantillasMT(), getPerfilesEnvio()])
      listas.value = l
      plantillas.value = p
      perfiles.value = pe.filter(x => x.estado === 'Activo')
      cargado = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'No se pudo conectar con MailerTurbo.'
    } finally {
      cargando.value = false
    }
  }

  const nuevaLista = async (titulo: string): Promise<ListaMT> => {
    const lista = await crearLista(titulo)
    listas.value = [lista, ...listas.value]
    return lista
  }

  return { listas, plantillas, perfiles, cargando, error, cargar, nuevaLista }
}
