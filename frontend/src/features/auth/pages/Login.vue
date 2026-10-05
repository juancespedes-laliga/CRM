<template>
  <div class="min-h-dvh w-full flex flex-col lg:flex-row bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 font-sans antialiased overflow-x-hidden">
    <!-- ── Panel de marca ─────────────────────────────────────────────── -->
    <section class="panel-marca relative overflow-hidden text-white lg:w-1/2 lg:min-h-dvh flex flex-col justify-between gap-6 px-6 py-6 sm:px-10 sm:py-8 lg:px-12 lg:py-10 xl:px-16 xl:py-14">
      <!-- Brillos de fondo: tres luces difusas que se desplazan muy despacio -->
      <div class="brillo brillo-rosa" aria-hidden="true"></div>
      <div class="brillo brillo-violeta" aria-hidden="true"></div>
      <div class="brillo brillo-celeste" aria-hidden="true"></div>
      <div class="textura" aria-hidden="true"></div>
      <div class="barrido" aria-hidden="true"></div>

      <div class="relative z-10 flex items-center gap-3">
        <div class="bg-white p-1.5 rounded-xl shadow-md shadow-blue-950/30">
          <span class="text-blue-700 font-black text-sm tracking-tight">PL</span>
        </div>
        <div>
          <span class="text-[9px] xl:text-[10px] text-blue-200 block font-bold uppercase tracking-wider leading-none">Plataforma Institucional</span>
          <h1 class="text-sm xl:text-base font-black tracking-tight text-white uppercase leading-tight">Mercadeo</h1>
        </div>
      </div>

      <div class="relative z-10 max-w-md xl:max-w-xl 2xl:max-w-3xl space-y-3 sm:space-y-5 xl:space-y-6 lg:my-auto">
        <div class="inline-flex items-center gap-2 bg-white/10 border border-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-[10px] xl:text-[11px] font-black uppercase tracking-wider text-pink-200 shadow-[0_0_24px_-4px_rgba(244,114,182,0.6)]">
          🎗️ 50 Años Salvando Vidas
        </div>
        <h2 class="text-xl sm:text-2xl lg:text-3xl xl:text-4xl 2xl:text-[2.75rem] font-black tracking-tight leading-[1.1] text-balance">
          Cada Plan Liga que vendemos <br>
          <span class="titulo-brillo">acerca la prevención a más personas</span>
        </h2>
        <!-- Lo que se trabaja aquí, en una lista corta y ordenada -->
        <ul class="hidden sm:grid gap-2.5 xl:gap-3 max-w-md pt-1">
          <li v-for="f in FUNCIONES" :key="f.titulo" class="funcion flex items-center gap-3 rounded-xl px-3.5 py-2.5 xl:py-3">
            <span class="w-8 h-8 xl:w-9 xl:h-9 rounded-lg bg-white/15 flex items-center justify-center shrink-0" :style="{ color: f.color }">
              <component :is="f.icono" :size="16" />
            </span>
            <span class="min-w-0">
              <span class="block text-[13px] xl:text-sm font-bold text-white leading-tight">{{ f.titulo }}</span>
              <span class="block text-[11px] xl:text-xs text-blue-100/80 leading-snug">{{ f.detalle }}</span>
            </span>
          </li>
        </ul>
        <p class="hidden sm:flex items-center gap-2 text-xs xl:text-sm font-semibold text-blue-100/90">
          <span class="w-6 h-px bg-blue-200/60"></span> Todo en un mismo lugar
        </p>
      </div>

      <div class="relative z-10 hidden lg:flex text-[10px] xl:text-[11px] text-blue-200/80 font-medium justify-between items-center pt-4 border-t border-white/15">
        <span>© 2026 Fundación La Liga.</span>
        <span class="font-mono">v3.5.0</span>
      </div>
    </section>

    <!-- ── Formulario ─────────────────────────────────────────────────── -->
    <!-- En pantallas de escritorio bajas (≤ 720 px de alto) se compactan los espacios verticales
         para que el formulario completo quepa sin scroll (clases [@media(...and(max-height:720px))]). -->
    <section class="panel-formulario relative flex-1 flex items-center justify-center px-6 py-10 sm:px-10 lg:px-12 lg:py-8 [@media(min-width:1024px)_and_(max-height:720px)]:py-6">
      <div class="w-full max-w-sm xl:max-w-md 2xl:max-w-lg space-y-6 xl:space-y-8 [@media(min-width:1024px)_and_(max-height:720px)]:space-y-4 animate-fadeIn">
        <div class="space-y-5 xl:space-y-7 [@media(min-width:1024px)_and_(max-height:720px)]:space-y-3 text-center">
          <!-- El PNG trae margen transparente: se recorta al área útil del logo -->
          <div class="logo-recorte mx-auto w-[220px] sm:w-[250px] lg:w-[270px] xl:w-[310px] 2xl:w-[350px] max-w-full [@media(min-width:1024px)_and_(max-height:720px)]:w-[220px]">
            <img src="/logo-liga-50.png" alt="Fundación La Liga - 50 Años" class="select-none pointer-events-none" />
          </div>
          <div>
            <h3 class="text-lg xl:text-xl 2xl:text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight">Iniciar Sesión</h3>
            <p class="text-xs xl:text-sm text-slate-500 dark:text-slate-400 mt-1">Ingresa tus credenciales autorizadas por TI.</p>
          </div>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4 xl:space-y-5 [@media(min-width:1024px)_and_(max-height:720px)]:space-y-3">
          <div class="space-y-1.5">
            <label for="login-usuario" class="text-[10px] xl:text-[11px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Usuario</label>
            <div class="relative">
              <User :size="15" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" />
              <input
                id="login-usuario"
                v-model="form.username"
                type="text"
                required
                autocomplete="username"
                placeholder="ejemplo"
                class="campo w-full h-11 xl:h-12 pl-10 pr-4 text-sm"
              />
            </div>
          </div>

          <div class="space-y-1.5">
            <label for="login-clave" class="text-[10px] xl:text-[11px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Contraseña</label>
            <div class="relative">
              <Lock :size="15" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" />
              <input
                id="login-clave"
                v-model="form.password"
                :type="mostrarClave ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="••••••••••••"
                class="campo w-full h-11 xl:h-12 pl-10 pr-11 text-sm"
              />
              <button
                type="button"
                @click="mostrarClave = !mostrarClave"
                :title="mostrarClave ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                :aria-label="mostrarClave ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              >
                <EyeOff v-if="mostrarClave" :size="15" />
                <Eye v-else :size="15" />
              </button>
            </div>
          </div>

          <label class="flex items-center gap-2 cursor-pointer select-none w-fit">
            <input type="checkbox" v-model="form.rememberMe" class="w-3.5 h-3.5 accent-blue-600" />
            <span class="text-xs text-slate-500 dark:text-slate-400 font-medium">Recordar sesión</span>
          </label>

          <div v-if="errorMsg" class="p-2.5 bg-red-50 dark:bg-red-950/40 border border-red-100 dark:border-red-800 rounded-xl text-xs font-semibold text-red-600 dark:text-red-400 flex items-center gap-2 animate-fadeIn">
            <AlertCircle :size="14" class="shrink-0" /> {{ errorMsg }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="boton-acceder group relative overflow-hidden w-full h-11 xl:h-12 rounded-xl text-white font-black text-xs xl:text-sm uppercase tracking-widest flex items-center justify-center gap-2 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <span class="destello" aria-hidden="true"></span>
            <span v-if="loading" class="relative animate-spin inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full"></span>
            <span class="relative">{{ loading ? 'Autenticando...' : 'Acceder' }}</span>
          </button>
        </form>

        <div class="pt-4 border-t border-slate-100 dark:border-slate-800 text-center">
          <p class="text-[11px] xl:text-xs text-slate-400 dark:text-slate-500 font-medium">
            ¿Problemas de acceso? Contacta a <a href="mailto:soporte@fundacionlaliga.org" class="text-blue-600 dark:text-blue-400 font-bold hover:underline">Soporte TI</a>
          </p>
        </div>

        <p class="lg:hidden text-center text-[10px] text-slate-400 dark:text-slate-500">© 2026 Fundación La Liga · v3.5.0</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Eye, EyeOff, AlertCircle, HeartPulse, Megaphone, UsersRound } from 'lucide-vue-next'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login } = useAuth()

const loading = ref<boolean>(false)
const errorMsg = ref<string>('')
const mostrarClave = ref(false)

const FUNCIONES = [
  { titulo: 'Plan Liga', detalle: 'Afiliaciones, renovaciones y descuentos', icono: HeartPulse, color: '#f9a8d4' },
  { titulo: 'Campañas de mercadeo', detalle: 'Correos, plantillas y audiencias', icono: Megaphone, color: '#fde68a' },
  { titulo: 'Grupos de interés', detalle: 'Listas por categoría para cada gestión', icono: UsersRound, color: '#bfdbfe' },
]

const form = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const handleLogin = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    await login({ username: form.username, password: form.password })
    router.push('/dashboard')
  } catch (error) {
    errorMsg.value = error instanceof Error ? error.message : 'Credenciales inválidas o cuenta sin acceso a la plataforma.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── Panel de marca ──────────────────────────────────────────────── */
.panel-marca {
  background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 45%, #1e3a8a 100%);
}
.brillo {
  position: absolute;
  border-radius: 9999px;
  filter: blur(70px);
  pointer-events: none;
  will-change: transform;
}
.brillo-rosa {
  width: 26rem; height: 26rem; top: -8rem; left: -8rem;
  background: rgba(244, 114, 182, 0.30);
  animation: deriva-a 18s ease-in-out infinite alternate;
}
.brillo-violeta {
  width: 24rem; height: 24rem; bottom: -9rem; right: -7rem;
  background: rgba(167, 139, 250, 0.30);
  animation: deriva-b 22s ease-in-out infinite alternate;
}
.brillo-celeste {
  width: 30rem; height: 30rem; top: 35%; left: 30%;
  background: rgba(96, 165, 250, 0.28);
  animation: deriva-c 26s ease-in-out infinite alternate;
}
/* Textura de puntos muy tenue: le da profundidad al azul sin distraer */
.textura {
  position: absolute; inset: 0; pointer-events: none; opacity: 0.12;
  background-image: radial-gradient(rgba(255, 255, 255, 0.55) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse at 30% 40%, #000 0%, transparent 70%);
}
@keyframes deriva-a { to { transform: translate(5rem, 4rem) scale(1.1); } }
@keyframes deriva-b { to { transform: translate(-4rem, -5rem) scale(1.15); } }
@keyframes deriva-c { to { transform: translate(-5rem, 3rem) scale(0.9); } }

/* Destello que cruza el panel de vez en cuando, igual al del botón Acceder */
.barrido {
  position: absolute; top: -20%; bottom: -20%; left: -60%; width: 40%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.10), transparent);
  transform: skewX(-18deg);
  pointer-events: none;
  animation: barrido 9s ease-in-out infinite;
}
@keyframes barrido {
  0%, 55% { left: -60%; }
  85%, 100% { left: 130%; }
}

/* Cada función: vidrio esmerilado con un resplandor suave, como el botón Acceder */
.funcion {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(6px);
  box-shadow: 0 10px 28px -14px rgba(147, 197, 253, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.10);
  transition: transform .25s, box-shadow .25s, background-color .25s;
}
.funcion:hover {
  transform: translateX(4px);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 12px 30px -12px rgba(244, 114, 182, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

/* Título con degradado rosa → blanco → dorado y un leve resplandor */
.titulo-brillo {
  background: linear-gradient(90deg, #f9a8d4 0%, #ffffff 50%, #fcd34d 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0 18px rgba(249, 168, 212, 0.35));
}

/* ── Formulario ──────────────────────────────────────────────────── */
/* Tono muy suave de fondo (rosa arriba a la derecha, azul abajo a la izquierda) */
.panel-formulario {
  background:
    radial-gradient(circle at 100% 0%, rgba(236, 72, 153, 0.07), transparent 45%),
    radial-gradient(circle at 0% 100%, rgba(37, 99, 235, 0.07), transparent 45%);
}
.logo-recorte { aspect-ratio: 1630 / 415; overflow: hidden; }
.logo-recorte img { display: block; width: 117.8%; max-width: none; margin: -19.94% 0 0 -9.51%; }

.campo {
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #0f172a;
  outline: none;
  transition: border-color .2s, box-shadow .2s, background-color .2s;
}
.campo::placeholder { color: #94a3b8; }
.campo:focus {
  border-color: #2563eb;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12), 0 6px 20px -8px rgba(37, 99, 235, 0.45);
}
:global(.dark) .campo { border-color: #334155; background: #1e293b; color: #f1f5f9; }
:global(.dark) .campo:focus { background: #0f172a; border-color: #60a5fa; }

/* Botón con brillo: sombra azul que pasa a rosa al pasar el mouse + destello que lo cruza */
.boton-acceder {
  background: linear-gradient(90deg, #1d4ed8, #1e40af);
  box-shadow: 0 10px 24px -10px rgba(29, 78, 216, 0.75);
}
.boton-acceder:hover:not(:disabled) {
  background: linear-gradient(90deg, #ec4899, #db2777);
  box-shadow: 0 12px 28px -10px rgba(236, 72, 153, 0.75);
  transform: translateY(-1px);
}
.boton-acceder:focus-visible { outline: 3px solid rgba(37, 99, 235, 0.35); outline-offset: 2px; }
.destello {
  position: absolute; top: 0; bottom: 0; left: -40%; width: 35%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.35), transparent);
  transform: skewX(-20deg);
  transition: left .7s ease;
}
.boton-acceder:hover .destello { left: 110%; }

.animate-fadeIn {
  animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .brillo, .animate-fadeIn, .barrido { animation: none; }
  .barrido { display: none; }
  .destello { display: none; }
}
</style>
