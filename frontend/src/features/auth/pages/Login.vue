<template>
  <div class="min-h-dvh md:h-dvh bg-slate-50 dark:bg-slate-900 flex flex-col md:flex-row antialiased text-slate-800 dark:text-slate-100 font-sans w-full overflow-hidden">
    
    <div class="w-full md:w-1/2 bg-gradient-to-br from-blue-800 via-blue-700 to-blue-900 p-5 sm:p-8 flex flex-col justify-between relative overflow-hidden text-white md:h-dvh">
      <div class="brillo-a absolute -top-24 -left-24 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
      <div class="brillo-b absolute -bottom-24 -right-24 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <!-- Destello que cruza el panel de vez en cuando -->
      <div class="barrido" aria-hidden="true"></div>

      <div class="escala flex items-center gap-3 relative z-10">
        <div class="bg-white p-1.5 rounded-xl shadow-md">
          <span class="text-blue-700 font-black text-sm tracking-tight">PL</span>
        </div>
        <div>
          <span class="text-[9px] text-blue-200 block font-bold uppercase tracking-wider leading-none">Plataforma Institucional</span>
          <h1 class="text-sm font-black tracking-tight text-white uppercase leading-tight">Mercadeo</h1>
        </div>
      </div>

      <div class="escala my-auto max-w-md xl:max-w-xl 2xl:max-w-2xl space-y-3 sm:space-y-6 relative z-10 py-4 md:py-0">
        <div class="inline-flex items-center gap-2 bg-blue-600/40 border border-blue-500/30 px-3 py-1 rounded-full text-[10px] xl:text-[11px] font-black uppercase tracking-wider text-pink-300">
          🎗️ 50 Años Salvando Vidas
        </div>
        <h2 class="text-2xl sm:text-3xl md:text-4xl xl:text-5xl 2xl:text-6xl font-black tracking-tight leading-tight">
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-pink-300 via-white to-amber-300">
            Consola Centralizada
          </span>
        </h2>
        <p class="hidden sm:block text-xs md:text-sm xl:text-base 2xl:text-lg text-blue-100 leading-relaxed font-medium">
          Accede al ecosistema comercial para maximizar nuestro impacto .
        </p>
      </div>

      <div class="escala hidden sm:flex text-[10px] text-blue-300/80 font-medium justify-between items-center relative z-10 pt-4 border-t border-blue-600/40">
        <span>© 2026 Fundación La Liga.</span>
        <span class="font-mono">v3.5.0</span>
      </div>
    </div>

    <div class="w-full md:w-1/2 bg-white dark:bg-slate-900 flex items-center justify-center p-6 sm:p-12 md:px-16 md:py-10 [@media(min-width:768px)_and_(max-height:820px)]:py-5 md:h-dvh md:overflow-y-auto relative">
      <div class="escala w-full max-w-sm xl:max-w-md 2xl:max-w-lg space-y-5 sm:space-y-8 [@media(min-width:768px)_and_(max-height:820px)]:space-y-4 animate-fadeIn">

        <div class="text-center space-y-2 sm:space-y-4 [@media(min-width:768px)_and_(max-height:820px)]:space-y-1">
          <div class="flex justify-center">
            <img
              src="/logo-liga-50.png"
              alt="Fundación La Liga - 50 Años"
              class="w-full max-w-[280px] sm:max-w-[370px] xl:max-w-[440px] 2xl:max-w-[500px] [@media(min-width:768px)_and_(max-height:820px)]:max-w-[310px] h-auto object-contain select-none pointer-events-none"
            />
          </div>

          <div class="pt-1 sm:pt-2">
            <h3 class="text-xl xl:text-2xl 2xl:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">Iniciar Sesión</h3>
            <p class="text-sm xl:text-base text-slate-400 dark:text-slate-500 mt-1">Ingresa tus credenciales autorizadas por TI.</p>
          </div>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-5 [@media(min-width:768px)_and_(max-height:820px)]:space-y-3">

          <div class="space-y-2.5 [@media(min-width:768px)_and_(max-height:820px)]:space-y-1.5">
            <label class="text-sm xl:text-base font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider block">Usuario</label>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 dark:text-slate-500 text-xs pointer-events-none"></span>
              <input
                v-model="form.username"
                type="text"
                required
                placeholder="ejemplo@laliga.org"
                class="w-full bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 rounded-xl border border-slate-200/80 dark:border-slate-700 pl-9 pr-4 h-12 xl:h-14 [@media(min-width:768px)_and_(max-height:820px)]:h-12 text-lg xl:text-xl font-medium focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-all shadow-2xs"
              />
            </div>
          </div>

          <div class="space-y-2.5 [@media(min-width:768px)_and_(max-height:820px)]:space-y-1.5">
            <div class="flex justify-between items-center">
              <label class="text-sm xl:text-base font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider block">Contraseña</label>
              <a href="#" class="text-sm xl:text-base font-bold text-pink-500 dark:text-pink-400 hover:underline">¿La olvidaste?</a>
            </div>
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 dark:text-slate-500 text-xs pointer-events-none"></span>
              <input
                v-model="form.password"
                :type="mostrarClave ? 'text' : 'password'"
                required
                placeholder="••••••••••••"
                class="w-full bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 rounded-xl border border-slate-200/80 dark:border-slate-700 pl-9 pr-14 h-12 xl:h-14 [@media(min-width:768px)_and_(max-height:820px)]:h-12 font-medium focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-all shadow-2xs"
                :class="!mostrarClave && form.password ? 'text-2xl xl:text-3xl tracking-widest' : 'text-lg xl:text-xl'"
              />
              <button
                type="button"
                @click="mostrarClave = !mostrarClave"
                :title="mostrarClave ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                :aria-label="mostrarClave ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                class="absolute right-2 top-1/2 -translate-y-1/2 w-11 h-11 rounded-lg flex items-center justify-center text-slate-600 dark:text-slate-300 hover:text-blue-700 dark:hover:text-blue-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              >
                <EyeOff v-if="mostrarClave" :size="25" :stroke-width="2.5" />
                <Eye v-else :size="25" :stroke-width="2.5" />
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between pt-1">
            <label class="flex items-center gap-2 cursor-pointer select-none">
              <input type="checkbox" v-model="form.rememberMe" class="w-3.5 h-3.5 text-blue-600 border-slate-300 dark:border-slate-600 rounded focus:ring-blue-500 bg-slate-50 dark:bg-slate-800" />
              <span class="text-sm xl:text-base text-slate-500 dark:text-slate-400 font-medium">Recordar sesión</span>
            </label>
          </div>

          <div v-if="errorMsg" class="p-2.5 bg-red-50 dark:bg-red-950/40 border border-red-100 dark:border-red-800 rounded-xl text-[11px] font-semibold text-red-600 dark:text-red-400 flex items-center gap-2 animate-fadeIn">
            <span></span> {{ errorMsg }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="group relative overflow-hidden w-full bg-gradient-to-r from-blue-700 to-blue-800 hover:from-pink-500 hover:to-pink-600 text-white font-black text-sm xl:text-base uppercase tracking-widest h-11 xl:h-12 [@media(min-width:768px)_and_(max-height:820px)]:h-11 rounded-xl shadow-md shadow-blue-700/10 hover:shadow-pink-500/10 transition-all duration-300 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-center flex items-center justify-center gap-2"
          >
            <span class="destello" aria-hidden="true"></span>
            <span v-if="loading" class="relative animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
            <span class="relative">{{ loading ? 'Autenticando...' : 'Acceder' }}</span>
          </button>
        </form>

        <div class="pt-4 [@media(min-width:768px)_and_(max-height:820px)]:pt-2 border-t border-slate-100 dark:border-slate-800 text-center">
          <p class="text-sm xl:text-base text-slate-400 dark:text-slate-500 font-medium">
            ¿Problemas de acceso? Contacta a <a href="mailto:soporte@fundacionlaliga.org" class="text-blue-600 dark:text-blue-400 font-bold hover:underline">Soporte TI</a>
          </p>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Eye, EyeOff } from 'lucide-vue-next'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login } = useAuth()

const loading = ref<boolean>(false)
const errorMsg = ref<string>('')
const mostrarClave = ref(false)

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
    errorMsg.value = error instanceof Error ? error.message : 'Credenciales inválidas o cuenta no activa en consola.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Todo el contenido del login un 10% más pequeño (letras, campos, logo y espacios) */
.escala { zoom: 0.9; }

/* Destellos: los dos brillos de fondo se desplazan despacio y un barrido cruza el panel */
.brillo-a { animation: deriva-a 18s ease-in-out infinite alternate; }
.brillo-b { animation: deriva-b 22s ease-in-out infinite alternate; }
@keyframes deriva-a { to { transform: translate(5rem, 4rem) scale(1.1); } }
@keyframes deriva-b { to { transform: translate(-4rem, -5rem) scale(1.15); } }
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
/* Destello que cruza el botón Acceder al pasar el mouse */
.destello {
  position: absolute; top: 0; bottom: 0; left: -40%; width: 35%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.35), transparent);
  transform: skewX(-20deg);
  transition: left .7s ease;
}
.group:hover .destello { left: 110%; }

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
  .brillo-a, .brillo-b, .animate-fadeIn { animation: none; }
  .barrido, .destello { display: none; }
}
</style>