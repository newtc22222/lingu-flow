import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

const TOKEN_KEY = 'token';
const GUEST_TOKEN_KEY = 'guest_token';

/**
 * Single source of truth for auth state. Previously `App.vue` derived
 * `isAuthenticated` from a one-shot `localStorage` read in `onMounted`, which
 * meant nothing re-rendered when the token changed. The router guard needs a
 * reactive answer on every navigation, so the token lives here instead.
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));

  const isAuthenticated = computed(() => Boolean(token.value));

  /** Persist a freshly issued token. `isGuest` also keeps the guest token so a
   * later register/login call can migrate the guest's data across. */
  function setToken(next: string, isGuest = false) {
    token.value = next;
    localStorage.setItem(TOKEN_KEY, next);
    if (isGuest) {
      localStorage.setItem(GUEST_TOKEN_KEY, next);
    } else {
      localStorage.removeItem(GUEST_TOKEN_KEY);
    }
  }

  function logout() {
    token.value = null;
    localStorage.removeItem(TOKEN_KEY);
  }

  return { token, isAuthenticated, setToken, logout };
});
