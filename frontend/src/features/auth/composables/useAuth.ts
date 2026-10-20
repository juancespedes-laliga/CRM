import { ref } from 'vue'
import { decodeJwt } from 'jose'
import { login as loginRequest, getMe } from '../services/auth.api'
import type { AuthResponse, LoginRequest, MeResponse } from '../types/auth'

const STORAGE_KEY = 'auth_session'

type Session = AuthResponse

function isTokenExpired(token: string): boolean {
  try {
    const { exp } = decodeJwt(token)
    if (!exp) return false
    return Date.now() >= exp * 1000
  } catch {
    return true
  }
}

function readSession(): Session | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Session
    if (isTokenExpired(parsed.token)) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    return null
  }
}

function toMe(s: Session): MeResponse {
  const { token: _token, ...rest } = s
  return rest
}

const session = ref<Session | null>(readSession())
const isAuthenticated = ref(session.value !== null)
const me = ref<MeResponse | null>(session.value ? toMe(session.value) : null)

// Endpoints como POST /api/bitacora/ ya no reciben el usuario en el body: lo resuelven
// ellos mismos a partir del Bearer token (username → usuario_id en su propia tabla).
// Este header es lo único que hay que mandar para que quede identificado.
export function authHeader(): Record<string, string> {
  return session.value ? { Authorization: `Bearer ${session.value.token}` } : {}
}

// Punto único para consultar permisos en toda la app: "modulo:accion", ej.
// tienePermiso('contactos:gestionar'). Vienen del login (y de /me al
// refrescar), ver AuthRepository.obtener_permisos en el backend.
export function tienePermiso(permiso: string): boolean {
  return session.value?.permisos.includes(permiso) ?? false
}

// Atajo para gatear una pantalla/tabla completa: si el módulo no tiene
// `ver`, ni siquiera debería mostrarse en el menú (eso se resuelve aparte
// en MainLayout). `gestionar` cubre crear/editar; `eliminar` es su propio
// permiso porque algunos roles pueden editar pero no borrar (ej. Publicidad
// en campañas: ver/gestionar/eliminar; Comunicaciones en bitácora: solo
// ver/eliminar, sin gestionar).
export function permisosDeModulo(modulo: string) {
  return {
    ver: tienePermiso(`${modulo}:ver`),
    gestionar: tienePermiso(`${modulo}:gestionar`),
    eliminar: tienePermiso(`${modulo}:eliminar`),
  }
}

export function useAuth() {
  const login = async (credentials: LoginRequest) => {
    const result = await loginRequest(credentials)
    session.value = result
    isAuthenticated.value = true
    me.value = toMe(result)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(result))
  }

  const logout = () => {
    session.value = null
    isAuthenticated.value = false
    me.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  // Verifica el token vigente y cierra la sesión si ya expiró. Úsalo antes de
  // decidir si una ruta protegida puede renderizarse.
  const checkSession = (): boolean => {
    if (session.value && isTokenExpired(session.value.token)) {
      logout()
    }
    return isAuthenticated.value
  }

  // Refresca nombres/rol contra /api/auth/me. Si falla, conserva los datos
  // que ya vinieron del login en vez de romper la UI.
  const fetchMe = async () => {
    if (!session.value) return
    try {
      me.value = await getMe(session.value.token)
      // Los permisos también se refrescan (tienePermiso lee la sesión): así un
      // permiso nuevo se ve al navegar, sin cerrar sesión.
      if (session.value) {
        session.value = { ...session.value, permisos: me.value.permisos ?? session.value.permisos }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(session.value))
      }
    } catch {
      // se mantiene el último valor conocido
    }
  }

  return { isAuthenticated, session, me, login, logout, checkSession, fetchMe }
}