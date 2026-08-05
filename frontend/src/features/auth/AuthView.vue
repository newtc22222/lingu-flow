<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import AppButton from '@/shared/components/AppButton.vue'
import { useAuthStore } from './store/authStore'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

/** Every successful credential exchange lands here: persist, then hand off to
 * the router. The guard on `/dashboard` re-reads the store, so the token has to
 * be committed before we navigate. */
async function completeAuth(token: string, isGuest = false) {
  auth.setToken(token, isGuest)
  await router.push({ name: 'dashboard' })
}

const mode = ref<'login' | 'signup' | 'forgot'>('login')
const username = ref('')
const email = ref('')
const password = ref('')
const errorMsg = ref('')
const isLoading = ref(false)
const googleBtnRef = ref<HTMLElement | null>(null)
const forgotEmail = ref('')
const forgotSubmitted = ref(false)

function switchMode(next: 'login' | 'signup' | 'forgot') {
  mode.value = next
  errorMsg.value = ''
  forgotEmail.value = ''
  forgotSubmitted.value = false
}

async function handleSubmit() {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const guestToken = localStorage.getItem('guest_token')
    const endpoint = mode.value === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body =
      mode.value === 'login'
        ? { email: email.value, password: password.value }
        : {
            username: username.value,
            email: email.value,
            password: password.value,
            guestToken: guestToken || undefined,
          }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()

    if (!res.ok) {
      errorMsg.value =
        data.error ||
        (mode.value === 'login' ? t('auth.errors.loginFailed') : t('auth.errors.signupFailed'))
      return
    }

    await completeAuth(data.token)
  } catch (err) {
    errorMsg.value = t('auth.errors.generic')
  } finally {
    isLoading.value = false
  }
}

async function handleForgotSubmit() {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const res = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: forgotEmail.value }),
    })
    if (res.ok) {
      forgotSubmitted.value = true
    } else {
      const data = await res.json()
      errorMsg.value = data.error || t('auth.errors.forgotFailed')
    }
  } catch (err) {
    errorMsg.value = t('auth.errors.generic')
  } finally {
    isLoading.value = false
  }
}

async function handleGuestLogin() {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const guestToken = localStorage.getItem('guest_token')
    const res = await fetch('/api/auth/guest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ guestToken: guestToken || undefined }),
    })
    const data = await res.json()
    if (res.ok) {
      await completeAuth(data.token, true)
    } else {
      errorMsg.value = data.error || t('auth.errors.guestFailed')
    }
  } catch (err) {
    errorMsg.value = t('auth.errors.guestGeneric')
  } finally {
    isLoading.value = false
  }
}

async function handleGoogleCallback(response: { credential: string }) {
  try {
    const guestToken = localStorage.getItem('guest_token')
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential, guestToken: guestToken || undefined }),
    })
    const data = await res.json()
    if (res.ok) {
      await completeAuth(data.token)
    } else {
      errorMsg.value = data.error || t('auth.errors.googleFailed')
    }
  } catch (err) {
    errorMsg.value = t('auth.errors.googleGeneric')
  }
}

onMounted(() => {
  if (window.google) {
    window.google.accounts.id.initialize({
      client_id: 'DUMMY_CLIENT_ID', // Replace with real ID
      callback: handleGoogleCallback,
    })
    if (googleBtnRef.value) {
      window.google.accounts.id.renderButton(googleBtnRef.value, {
        theme: 'filled_black',
        size: 'large',
        width: '100%',
      })
    }
  }
})
</script>

<template>
  <div class="auth-screen">
    <div class="auth-wordmark font-pixel" aria-hidden="false">
      LINGUFLOW<span class="auth-cursor" aria-hidden="true">▌</span>
    </div>
    <p class="auth-tagline font-label">{{ t('auth.tagline') }}</p>

    <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="auth-cabinet">
      <div class="auth-inner">
        <div v-if="mode !== 'forgot'" class="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'login'"
            class="auth-tab font-label"
            :class="{ 'auth-tab--active': mode === 'login' }"
            @click="switchMode('login')"
          >
            {{ t('auth.login') }}
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'signup'"
            class="auth-tab font-label"
            :class="{ 'auth-tab--active': mode === 'signup' }"
            @click="switchMode('signup')"
          >
            {{ t('auth.signup') }}
          </button>
        </div>

        <form v-if="mode !== 'forgot'" class="auth-form" @submit.prevent="handleSubmit">
          <div v-if="errorMsg" class="auth-error font-label">{{ errorMsg }}</div>

          <div v-if="mode === 'signup'" class="arcade-field">
            <label class="arcade-label" for="auth-username">{{ t('auth.username') }}</label>
            <input id="auth-username" v-model="username" type="text" required class="arcade-input" />
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="auth-email">{{ t('auth.email') }}</label>
            <input id="auth-email" v-model="email" type="email" required class="arcade-input" />
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="auth-password">{{ t('auth.password') }}</label>
            <input id="auth-password" v-model="password" type="password" required class="arcade-input" />
          </div>

          <button
            v-if="mode === 'login'"
            type="button"
            class="auth-forgot-link font-label"
            @click="switchMode('forgot')"
          >
            {{ t('auth.forgotLink') }}
          </button>

          <AppButton type="submit" class="auth-submit-btn" :disabled="isLoading">
            {{
              isLoading
                ? mode === 'login'
                  ? t('auth.loggingIn')
                  : t('auth.creatingAccount')
                : mode === 'login'
                  ? t('auth.login')
                  : t('auth.createAccount')
            }}
          </AppButton>
        </form>

        <div v-if="mode === 'forgot'" class="auth-forgot">
          <div v-if="errorMsg" class="auth-error font-label">{{ errorMsg }}</div>

          <template v-if="!forgotSubmitted">
            <p class="auth-forgot-desc font-body">{{ t('auth.forgotDesc') }}</p>
            <form class="auth-form" @submit.prevent="handleForgotSubmit">
              <div class="arcade-field">
                <label class="arcade-label" for="auth-forgot-email">{{ t('auth.email') }}</label>
                <input
                  id="auth-forgot-email"
                  v-model="forgotEmail"
                  type="email"
                  required
                  class="arcade-input"
                />
              </div>

              <AppButton type="submit" class="auth-submit-btn" :disabled="isLoading">
                {{ isLoading ? t('auth.sending') : t('auth.sendResetLink') }}
              </AppButton>
            </form>
          </template>

          <p v-else class="auth-forgot-desc font-body">{{ t('auth.forgotSent') }}</p>

          <button type="button" class="auth-forgot-link font-label" @click="switchMode('login')">
            {{ t('auth.backToLogin') }}
          </button>
        </div>

        <template v-if="mode !== 'forgot'">
          <div class="auth-divider font-label">
            <span class="auth-divider-line" />
            <span>{{ t('auth.or') }}</span>
            <span class="auth-divider-line" />
          </div>

          <div ref="googleBtnRef" class="auth-google"></div>

          <AppButton variant="secondary" class="auth-guest-btn" :disabled="isLoading" @click="handleGuestLogin">
            {{ t('auth.guest') }}
          </AppButton>
        </template>
      </div>
    </PixelFrame>
  </div>
</template>

<style scoped>
.auth-screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10);
  overflow-y: auto;
}
.auth-wordmark {
  font-size: var(--font-size-2xl);
  color: var(--color-accent);
  letter-spacing: var(--tracking-normal);
}
.auth-cursor {
  margin-left: var(--space-2);
  animation: auth-blink 1s steps(1) infinite;
}
@keyframes auth-blink {
  50% {
    opacity: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .auth-cursor {
    animation: none;
  }
}
.auth-tagline {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  letter-spacing: var(--tracking-tight);
  margin: var(--space-4) 0 var(--space-9);
  text-align: center;
}
.auth-cabinet {
  width: 100%;
  max-width: 380px;
}
.auth-inner {
  padding: var(--space-9);
}
.auth-tabs {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-9);
}
.auth-tab {
  flex: 1;
  padding: var(--space-5);
  font-size: var(--font-size-base);
  letter-spacing: var(--tracking-tight);
  background: var(--surface-panel-border);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
}
.auth-tab--active {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
}
.auth-tab:hover:not(.auth-tab--active) {
  color: var(--text-primary);
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.auth-error {
  color: var(--status-danger);
  font-size: var(--font-size-base);
  background: var(--surface-page);
  border-left: var(--border-width-accent) solid var(--status-danger);
  padding: var(--space-5) var(--space-6);
}
.auth-submit-btn {
  width: 100%;
  margin-top: var(--space-3);
}
.auth-divider {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  margin: var(--space-8) 0 var(--space-7);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}
.auth-divider-line {
  flex: 1;
  height: 1px;
  background: var(--surface-panel-border);
}
.auth-google {
  margin-bottom: var(--space-6);
}
.auth-guest-btn {
  width: 100%;
  padding: var(--space-6);
}
.auth-tab:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.auth-forgot-link {
  align-self: flex-start;
  background: none;
  border: none;
  padding: 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-tight);
  cursor: pointer;
  text-decoration: underline;
}
.auth-forgot-link:hover {
  color: var(--text-primary);
}
.auth-forgot {
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.auth-forgot-desc {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  line-height: 1.5;
}
</style>
