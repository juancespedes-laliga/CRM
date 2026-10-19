import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: 'campanas',
    name: 'campanas',
    component: () => import('@/features/campanas/pages/List.vue'),
  },
  {
    path: 'campanas/mailerturbo',
    name: 'campanas-mailerturbo',
    component: () => import('@/features/mailerturbo/pages/MailerTurbo.vue'),
  },
  {
    path: 'campanas/estadisticas',
    name: 'campanas-estadisticas',
    component: () => import('@/features/mailerturbo/pages/Estadisticas.vue'),
  },
  {
    path: 'campanas/mailerturbo/:id(\\d+)',
    name: 'campanas-mailerturbo-detalle',
    component: () => import('@/features/mailerturbo/pages/CampanaDetalle.vue'),
  },
]

export default routes
