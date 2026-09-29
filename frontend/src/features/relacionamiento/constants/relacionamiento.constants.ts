import { Phone, Mail, Calendar, MessageCircle, MessageSquare, FileText } from 'lucide-vue-next'
import type { ActividadDraft, TipoActividad } from '../types/actividad'

export const TIPOS_ACTIVIDAD: TipoActividad[] = ['Llamada', 'Correo', 'Reunión', 'WhatsApp', 'Mensaje', 'Nota']

export const TIPO_META: Record<TipoActividad, { icono: unknown; color: string; bg: string }> = {
  'Llamada':  { icono: Phone,         color: '#2447F9', bg: '#EEF2FF' },
  'Correo':   { icono: Mail,          color: '#EC4899', bg: '#FCE7F3' },
  'Reunión':  { icono: Calendar,      color: '#C9A227', bg: '#FEF9C3' },
  'WhatsApp': { icono: MessageCircle, color: '#059669', bg: '#D1FAE5' },
  'Mensaje':  { icono: MessageSquare, color: '#7C3AED', bg: '#F3E8FF' },
  'Nota':     { icono: FileText,      color: '#c06e03', bg: '#E8EAF6' },
}

export const ACTIVIDAD_DRAFT_VACIO: ActividadDraft = {
  tipo: 'Llamada',
  contactoId: null, contactoNombre: '', contactoDocumento: '',
  empresaNombre: '',
  titularId: null, titularNombre: '', titularDocumento: '',
  accion: '', proximoPaso: '', proximoPasoFecha: '',
  fecha: new Date().toISOString().split('T')[0], oportunidadId: null,
}
