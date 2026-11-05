import type { RouteRecordRaw } from 'vue-router'
import { esModuloValido } from './constants/auditoria.constants'

// /auditoria es la pantalla de entrada (una tarjeta por módulo);
// /auditoria/:modulo es la auditoría de ese módulo ("todos" = todos a la vez).
const routes: RouteRecordRaw[] = [
  {
    path: 'auditoria',
    name: 'auditoria',
    component: () => import('./pages/Hub.vue'),
    meta: { permiso: 'auditoria:ver' },
  },
  {
    path: 'auditoria/:modulo',
    name: 'auditoria-modulo',
    component: () => import('./pages/List.vue'),
    meta: { permiso: 'auditoria:ver' },
    beforeEnter: (to) => (esModuloValido(to.params.modulo) ? true : '/auditoria'),
  },
]

export default routes
