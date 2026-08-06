<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
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

function handleGoogleClick() {
  if (window.google?.accounts?.id) {
    window.google.accounts.id.prompt()
  } else {
    errorMsg.value = t('auth.errors.googleFailed')
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
    <!-- CRT Scanline overlay effect -->
    <div class="auth-scanlines" aria-hidden="true"></div>

    <main class="auth-main">
      <!-- Header Section -->
      <header class="auth-header">
        <div class="auth-wordmark font-pixel" aria-hidden="false">
          LINGUFLOW<span class="auth-cursor" aria-hidden="true">▌</span>
        </div>
        <p class="auth-tagline font-label">{{ t('auth.tagline') }}</p>
      </header>

      <!-- Arcade Cabinet Container -->
      <div class="auth-cabinet">
        <!-- Corner Screw/Bolt Accents -->
        <div class="corner-screw corner-tl" aria-hidden="true"></div>
        <div class="corner-screw corner-tr" aria-hidden="true"></div>
        <div class="corner-screw corner-bl" aria-hidden="true"></div>
        <div class="corner-screw corner-br" aria-hidden="true"></div>

        <!-- Auth Tabs -->
        <div v-if="mode !== 'forgot'" class="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'login'"
            class="auth-tab font-label"
            :class="{ 'auth-tab--active': mode === 'login' }"
            @click="switchMode('login')"
          >
            [{{ t('auth.login') }}]
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'signup'"
            class="auth-tab font-label"
            :class="{ 'auth-tab--active': mode === 'signup' }"
            @click="switchMode('signup')"
          >
            [{{ t('auth.signup') }}]
          </button>
        </div>

        <div v-else class="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected="true"
            class="auth-tab auth-tab--active font-label"
          >
            [{{ t('auth.forgotLink') }}]
          </button>
        </div>

        <!-- Form Content Container -->
        <div class="auth-body">
          <form v-if="mode !== 'forgot'" class="auth-form" @submit.prevent="handleSubmit">
            <div v-if="errorMsg" class="auth-error font-label">{{ errorMsg }}</div>

            <div v-if="mode === 'signup'" class="arcade-field">
              <label class="arcade-label" for="auth-username">{{ t('auth.username') }}</label>
              <input id="auth-username" v-model="username" type="text" required class="arcade-input auth-recessed-input" />
            </div>

            <div class="arcade-field">
              <label class="arcade-label" for="auth-email">{{ t('auth.email') }}</label>
              <input id="auth-email" v-model="email" type="email" required :placeholder="t('auth.emailPlaceholder')" class="arcade-input auth-recessed-input" />
            </div>

            <div class="arcade-field">
              <label class="arcade-label" for="auth-password">{{ t('auth.password') }}</label>
              <input id="auth-password" v-model="password" type="password" required :placeholder="t('auth.passwordPlaceholder')" class="arcade-input auth-recessed-input" />
              <div v-if="mode === 'login'" class="auth-forgot-wrapper">
                <button
                  type="button"
                  class="auth-forgot-link font-label"
                  @click="switchMode('forgot')"
                >
                  {{ t('auth.forgotLink') }}
                </button>
              </div>
            </div>

            <AppButton type="submit" class="auth-submit-btn" :disabled="isLoading">
              <span>
                {{
                  isLoading
                    ? mode === 'login'
                      ? t('auth.loggingIn')
                      : t('auth.creatingAccount')
                    : mode === 'login'
                      ? t('auth.login')
                      : t('auth.createAccount')
                }}
              </span>
              <span class="auth-submit-icon" aria-hidden="true">→</span>
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
                    :placeholder="t('auth.emailPlaceholder')"
                    class="arcade-input auth-recessed-input"
                  />
                </div>

                <AppButton type="submit" class="auth-submit-btn" :disabled="isLoading">
                  <span>{{ isLoading ? t('auth.sending') : t('auth.sendResetLink') }}</span>
                  <span class="auth-submit-icon" aria-hidden="true">→</span>
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
              <span>[ {{ t('auth.or') }} ]</span>
              <span class="auth-divider-line" />
            </div>

            <div class="auth-secondary-actions">
              <div ref="googleBtnRef" class="auth-google">
                <button
                  type="button"
                  class="auth-google-fallback font-label"
                  :disabled="isLoading"
                  @click="handleGoogleClick"
                >
                  <svg class="auth-google-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="var(--brand-google-blue)" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="var(--brand-google-green)" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="var(--brand-google-yellow)" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="var(--brand-google-red)" />
                  </svg>
                  <span>{{ t('auth.google') }}</span>
                </button>
              </div>

              <AppButton variant="secondary" class="auth-guest-btn" :disabled="isLoading" @click="handleGuestLogin">
                {{ t('auth.guest') }}
              </AppButton>
            </div>
          </template>
        </div>
      </div>
    </main>

    <!-- Footer Component -->
    <footer class="auth-footer font-label">
      <div class="auth-footer-inner">
        <div class="auth-footer-brand">{{ t('auth.footerBrand') }}</div>
        <div class="auth-footer-links">
          <span class="auth-footer-link">{{ t('auth.footerProtocol') }}</span>
          <span class="auth-footer-link">{{ t('auth.footerDocs') }}</span>
          <span class="auth-footer-link">{{ t('auth.footerSupport') }}</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.auth-screen {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-8) var(--space-6);
  position: relative;
  background: var(--surface-page);
  color: var(--text-primary);
  box-sizing: border-box;
}

/* stylelint-disable-next-line function-disallowed-list -- CRT scanline gradient overlay */
.auth-scanlines {
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
  background-size: 100% 2px;
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 50;
}

.auth-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
  padding: var(--space-8) 0;
  z-index: 10;
  position: relative;
}

.auth-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: var(--space-9);
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
  color: var(--text-label-accent);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-wide);
  margin-top: var(--space-2);
  text-transform: uppercase;
}

.auth-cabinet {
  width: 100%;
  background: var(--surface-panel);
  border: var(--border-width-accent) solid var(--color-accent);
  position: relative;
  display: flex;
  flex-direction: column;
}

.corner-screw {
  position: absolute;
  width: var(--space-3);
  height: var(--space-3);
  border-radius: 9999px;
  background: var(--surface-panel-border);
  border: 1px solid var(--surface-page);
  z-index: 20;
}

.corner-tl {
  top: var(--space-2);
  left: var(--space-2);
}

.corner-tr {
  top: var(--space-2);
  right: var(--space-2);
}

.corner-bl {
  bottom: var(--space-2);
  left: var(--space-2);
}

.corner-br {
  bottom: var(--space-2);
  right: var(--space-2);
}

.auth-tabs {
  display: flex;
  width: 100%;
  border-bottom: var(--border-width-accent) solid var(--surface-panel-border);
}

.auth-tab {
  flex: 1;
  padding: var(--space-6) var(--space-4);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-wide);
  background: var(--surface-panel-border);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  text-align: center;
  text-transform: uppercase;
  transition: background 0.15s ease, color 0.15s ease;
}

.auth-tab--active {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
  border-bottom: var(--border-width-accent) solid var(--color-accent);
  font-weight: 700;
}

.auth-tab:hover:not(.auth-tab--active) {
  background: var(--state-hover-surface);
  color: var(--text-primary);
}

.auth-tab:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: -2px;
}

.auth-body {
  padding: var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.auth-recessed-input {
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- inset shadow effect */
  box-shadow: inset 0 2px 4px var(--ink);
  border: var(--space-1) solid var(--surface-panel-border);
  border-radius: 0;
  padding: var(--space-5) var(--space-6);
}

.auth-recessed-input:focus-visible {
  border-color: var(--color-accent);
  outline: none;
}

.auth-error {
  color: var(--status-danger);
  font-size: var(--font-size-base);
  background: var(--surface-page);
  border-left: var(--border-width-accent) solid var(--status-danger);
  padding: var(--space-5) var(--space-6);
}

.auth-forgot-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-2);
}

.auth-forgot-link {
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
  color: var(--color-accent);
}

.auth-submit-btn {
  width: 100%;
  margin-top: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
}

.auth-submit-icon {
  font-weight: 700;
  font-size: var(--font-size-lg);
}

.auth-divider {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  margin: var(--space-4) 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.auth-divider-line {
  flex: 1;
  height: 1px;
  background: var(--surface-panel-border);
}

.auth-secondary-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.auth-google {
  width: 100%;
}

.auth-google-fallback {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
  background: var(--surface-panel-border);
  color: var(--text-primary);
  border: var(--space-1) solid var(--surface-panel-border);
  cursor: pointer;
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
}

.auth-google-fallback:hover {
  background: var(--state-hover-surface);
}

.auth-google-icon {
  width: var(--space-8);
  height: var(--space-8);
}

.auth-guest-btn {
  width: 100%;
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

.auth-footer {
  width: 100%;
  border-top: var(--space-1) solid var(--surface-panel-border);
  background: var(--surface-page);
  padding: var(--space-6) var(--space-8);
  margin-top: var(--space-10);
  z-index: 10;
  position: relative;
}

.auth-footer-inner {
  max-width: 1024px;
  margin: 0 auto;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.auth-footer-brand {
  color: var(--color-accent);
  font-size: var(--font-size-md);
  font-weight: 700;
  letter-spacing: var(--tracking-normal);
}

.auth-footer-links {
  display: flex;
  gap: var(--space-6);
}

.auth-footer-link {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  cursor: pointer;
  transition: color 0.15s ease;
}

.auth-footer-link:hover {
  color: var(--color-accent);
}
</style>

