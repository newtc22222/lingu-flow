<script setup lang="ts">
import { ref, onMounted } from 'vue';

const emit = defineEmits(['login-success', 'go-to-signup']);

const email = ref('');
const password = ref('');
const errorMsg = ref('');
const isLoading = ref(false);
const googleBtnRef = ref<HTMLElement | null>(null);

const handleLogin = async () => {
  isLoading.value = true;
  errorMsg.value = '';
  
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      errorMsg.value = data.error || 'Login failed';
      return;
    }
    
    localStorage.setItem('token', data.token);
    // If they were a guest, they are now logged in as standard user
    localStorage.removeItem('guest_token');
    emit('login-success', data.user);
  } catch (err) {
    errorMsg.value = 'An error occurred during login.';
  } finally {
    isLoading.value = false;
  }
};

const handleGuestLogin = async () => {
  isLoading.value = true;
  try {
    const guestToken = localStorage.getItem('guest_token');
    const res = await fetch('/api/auth/guest', { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ guestToken: guestToken || undefined })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('guest_token', data.token);
      emit('login-success', data.user);
    } else {
      errorMsg.value = data.error || 'Guest login failed';
    }
  } catch (err) {
    errorMsg.value = 'Error during guest login';
  } finally {
    isLoading.value = false;
  }
};

const handleGoogleCallback = async (response: any) => {
  try {
    const guestToken = localStorage.getItem('guest_token');
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        credential: response.credential,
        guestToken: guestToken || undefined 
      })
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('token', data.token);
      localStorage.removeItem('guest_token');
      emit('login-success', data.user);
    } else {
      errorMsg.value = data.error || 'Google login failed';
    }
  } catch (err) {
    errorMsg.value = 'Error during Google login';
  }
};

onMounted(() => {
  if (window.google) {
    window.google.accounts.id.initialize({
      client_id: 'DUMMY_CLIENT_ID', // Replace with real ID
      callback: handleGoogleCallback
    });
    if (googleBtnRef.value) {
      window.google.accounts.id.renderButton(googleBtnRef.value, {
        theme: 'filled_black',
        size: 'large',
        width: '100%'
      });
    }
  }
});
</script>

<template>
  <div class="flex items-center justify-center h-full bg-slate-900 text-slate-100 p-4 overflow-y-auto">
    <div class="bg-slate-800 p-8 rounded-2xl border border-slate-700 w-full max-w-md shadow-2xl my-4">
      <h2 class="text-3xl font-bold text-center text-emerald-400 mb-8">Welcome Back</h2>
      
      <form @submit.prevent="handleLogin" class="flex flex-col gap-5">
        <div v-if="errorMsg" class="bg-rose-500/20 text-rose-400 p-3 rounded-lg text-sm border border-rose-500/30">
          {{ errorMsg }}
        </div>
        
        <div>
          <label class="block text-sm text-slate-400 mb-1">Email</label>
          <input 
            v-model="email" 
            type="email" 
            required
            class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-100 focus:border-emerald-500 focus:outline-none transition-colors"
          />
        </div>
        
        <div>
          <label class="block text-sm text-slate-400 mb-1">Password</label>
          <input 
            v-model="password" 
            type="password" 
            required
            class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-100 focus:border-emerald-500 focus:outline-none transition-colors"
          />
        </div>
        
        <button 
          type="submit" 
          :disabled="isLoading"
          class="w-full bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg p-3 font-semibold transition-colors mt-2 disabled:opacity-50"
        >
          {{ isLoading ? 'Logging in...' : 'Log In' }}
        </button>
      </form>
      
      <div class="my-6 flex items-center gap-4">
        <hr class="flex-1 border-slate-700">
        <span class="text-slate-500 text-sm">or</span>
        <hr class="flex-1 border-slate-700">
      </div>
      
      <div class="flex flex-col gap-4">
        <div ref="googleBtnRef" class="w-full"></div>
        <button 
          @click="handleGuestLogin"
          :disabled="isLoading"
          class="w-full bg-slate-700 hover:bg-slate-600 text-white rounded-lg p-3 font-semibold transition-colors disabled:opacity-50"
        >
          Continue as Guest
        </button>
      </div>

      <div class="mt-6 text-center text-slate-400 text-sm">
        Don't have an account? 
        <button @click="emit('go-to-signup')" class="text-emerald-400 hover:underline">Sign up</button>
      </div>
    </div>
  </div>
</template>
