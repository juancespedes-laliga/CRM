import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import MainLayout from '@/app/layouts/MainLayout.vue'
import AuthLayout from '@/app/layouts/AuthLayout.vue'

import { useAuth } from '@/features/auth/composables/useAuth'
import authRoutes from '@/features/auth/routes'
import dashboardRoutes from '@/features/dashboard/routes'
import planLigaRoutes from '@/features/plan-liga/routes'
import contactosRoutes from '@/features/contactos/routes'
import empresasRoutes from '@/features/empresas/routes'
import gruposInteresRoutes from '@/features/grupos-interes/routes'
import proveedoresRoutes from '@/features/proveedores/routes'
import oportunidadesRoutes from '@/features/oportunidades/routes'
import embudosRoutes from '@/features/embudos/routes'
import serviciosRoutes from '@/features/servicios/routes'
import campanasRoutes from '@/features/campanas/routes'
import relacionamientoRoutes from '@/features/relacionamiento/routes'
import importacionRoutes from '@/features/importacion/routes'
import automatizacionesRoutes from '@/features/automatizaciones/routes'
import usuariosRoutes from '@/features/usuarios/routes'
import configuracionRoutes from '@/features/configuracion/routes'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: AuthLayout,
    children: authRoutes,
  },
  {
    // Fuera de MainLayout a proposito: un usuario sin rol no debe ver el
    // menu/sidebar del CRM, solo este mensaje.
    path: '/sin-rol',
    name: 'sin-rol',
    component: () => import('@/features/auth/pages/SinRolAsignado.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      ...dashboardRoutes,
      ...planLigaRoutes,
      ...contactosRoutes,
      ...empresasRoutes,
      ...gruposInteresRoutes,
      ...proveedoresRoutes,
      ...oportunidadesRoutes,
      ...embudosRoutes,
      ...serviciosRoutes,
      ...campanasRoutes,
      ...relacionamientoRoutes,
      ...importacionRoutes,
      ...automatizacionesRoutes,
      ...usuariosRoutes,
      ...configuracionRoutes,
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from) => {
  const { checkSession, me, logout, fetchMe } = useAuth()
  const authenticated = checkSession()

  if (to.meta.requiresAuth && !authenticated) {
    return '/login'
  }

  if (to.path === '/login' && authenticated) {
    return '/'
  }

  // from.matched vacio = esta es la primera navegacion despues de una carga
  // de pagina real (F5, URL escrita a mano, etc.), no una navegacion dentro
  // de la SPA. Recargar estando en /sin-rol siempre manda a login, sin
  // importar si mientras tanto le asignaron rol o no - simplemente tiene
  // que volver a loguearse para entrar con lo que tenga en ese momento.
  if (authenticated && to.path === '/sin-rol' && from.matched.length === 0) {
    logout()
    return '/login'
  }

  // Antes de decidir con el rol, se refresca contra /auth/me: el rol que
  // quedo guardado en localStorage al loguearse puede estar desactualizado
  // si un admin se lo cambio o se lo quito despues (el JWT en si no siempre
  // permite detectar esto - un token emitido por el portal SSO externo no
  // trae "iat", asi que el chequeo de "token viejo" del backend no aplica
  // ahi). Se hace en cada navegacion protegida para que un cambio de rol se
  // note "al ver un menu", no solo cuando el usuario dispara una accion.
  if (authenticated && to.meta.requiresAuth) {
    const rolAntes = me.value?.role_crm ?? null
    await fetchMe()
    const rolAhora = me.value?.role_crm ?? null

    // Ya tenia un rol y ahora es distinto (se lo cambiaron) o desaparecio (se
    // lo quitaron): a diferencia del caso "nunca tuvo rol", aqui no tiene
    // sentido mostrar la pantalla informativa - hay que cerrar la sesion
    // vieja y que vuelva a loguearse con lo que le corresponda ahora.
    if (rolAntes !== null && rolAntes !== rolAhora) {
      logout()
      return '/login'
    }
  }

  // Autenticado pero sin rol de CRM asignado (incluye justo despues de
  // loguearse): bloquea cualquier vista y manda a la pantalla informativa,
  // sin cerrarle la sesion sola (excepto si ya esta ahi, para no quedar en
  // bucle de redirects).
  if (authenticated && !me.value?.role_crm && to.path !== '/sin-rol') {
    return '/sin-rol'
  }

  // Ya tiene rol pero intenta entrar a /sin-rol a mano: no tiene sentido, lo
  // manda al dashboard.
  if (authenticated && !!me.value?.role_crm && to.path === '/sin-rol') {
    return '/dashboard'
  }
})

export default router
