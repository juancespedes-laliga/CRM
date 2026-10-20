import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: 'embudos/afiliado/grupos', name: 'grupos-interes', component: () => import('./pages/List.vue') },
]

export default routes
