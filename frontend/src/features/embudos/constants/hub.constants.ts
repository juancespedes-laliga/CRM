import { RefreshCw, Bookmark } from 'lucide-vue-next'

export interface HubCard {
  titulo: string
  descripcion: string
  ruta: string
  icono: unknown
  color: string
  bg: string
}

export const HUB_CARDS: HubCard[] = [
  {
    titulo: 'Audiencias',
    descripcion: 'Arma una audiencia con filtros y actúa por correo o WhatsApp. Incluye los grupos de interés.',
    ruta: '/embudos/afiliado',
    icono: RefreshCw, color: '#EC4899', bg: '#FCE7F3',
  },
  {
    titulo: 'Segmentos guardados',
    descripcion: 'Grupos de personas listos para correo, WhatsApp o crear tareas.',
    ruta: '/segmentos',
    icono: Bookmark, color: '#C9A227', bg: '#FEF9C3',
  },
]
