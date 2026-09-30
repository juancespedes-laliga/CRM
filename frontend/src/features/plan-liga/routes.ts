import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: 'plan-liga', name: 'plan-liga', component: () => import('./pages/List.vue') },
  {
    path: 'plan-liga-vencimientos',
    name: 'plan-liga-vencimientos',
    component: () => import('./pages/RecordatoriosVencimiento.vue'),
  },
  {
    path: 'plan-liga-renovaciones',
    name: 'plan-liga-renovaciones',
    component: () => import('./pages/RenovacionesPorMes.vue'),
  },
]

export default routes
