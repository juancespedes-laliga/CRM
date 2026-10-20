<template>
  <div class="tableau-container">
    <tableau-viz
      v-if="jwtToken"
      id="tableau-viz"
      src="https://us-east-1.online.tableau.com/t/laliga-amasalvarvidas/views/Produccion-PlanLigaUso_17846654795520/Inicio-Produccion-PlanLigaUso"
      :token="jwtToken"
      width="100%"
      height="100%"
      toolbar="hidden"
    >
    </tableau-viz>

    <div v-else class="flex flex-col justify-center items-center h-full gap-3 text-slate-400 dark:text-slate-500">
      <svg class="animate-spin h-7 w-7 text-slate-900 font-bold dark:text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
      <span class="text-[13px] font-semibold text-slate-500 dark:text-slate-400">Autenticando tablero de forma segura…</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import '@tableau/embedding-api';
import { SignJWT } from 'jose';
import { v4 as uuidv4 } from 'uuid';

const jwtToken = ref(null);

const clientId = import.meta.env.VITE_TABLEAU_CLIENT_ID;
const secretId = import.meta.env.VITE_TABLEAU_SECRET_ID;
const secretValue = import.meta.env.VITE_TABLEAU_SECRET_VALUE;
const username = import.meta.env.VITE_TABLEAU_USERNAME;

const generarToken = async () => {
  try {
    const secret = new TextEncoder().encode(secretValue);
    
    const ahora = Math.floor(Date.now() / 1000) - 60; 

    const token = await new SignJWT({
      iss: clientId,
      sub: username,
      aud: 'tableau',
      scp: ['tableau:views:embed', 'tableau:metrics:embed'] 
    })
      .setProtectedHeader({ 
        alg: 'HS256',
        kid: secretId, 
        iss: clientId  
      })
      .setJti(uuidv4())
      .setIssuedAt(ahora) 
      .setExpirationTime(ahora + 300) 
      .sign(secret);

    return token;
  } catch (error) {
    console.error('Error al generar token:', error);
    return null;
  }
};

onMounted(async () => {
  const tokenGenerado = await generarToken();
  if (tokenGenerado) {
    jwtToken.value = tokenGenerado;
  }
});
</script>

<style scoped>
.tableau-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

#tableau-viz {
  flex: 1;
  display: block;
  width: 100%;
  height: 100%;
}
</style>
