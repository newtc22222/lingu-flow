<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PixelFrame from '@/shared/components/PixelFrame.vue'

const emit = defineEmits<{
  (e: 'auth-success', user: unknown): void
}>()

const mode = ref<'login' | 'signup'>('login')
const username = ref('')
const email = ref('')
const password = ref('')
const errorMsg = ref('')
const isLoading = ref(false)
const googleBtnRef = ref<HTMLElement | null>(null)

function switchMode(next: 'login' | 'signup') {
  mode.value = next
  errorMsg.value = ''
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
      errorMsg.value = data.error || (mode.value === 'login' ? 'Đăng nhập thất bại' : 'Đăng ký thất bại')
      return
    }

    localStorage.setItem('token', data.token)
    localStorage.removeItem('guest_token')
    emit('auth-success', data.user)
  } catch (err) {
    errorMsg.value = 'Đã xảy ra lỗi. Vui lòng thử lại.'
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
      localStorage.setItem('token', data.token)
      localStorage.setItem('guest_token', data.token)
      emit('auth-success', data.user)
    } else {
      errorMsg.value = data.error || 'Không thể vào chế độ khách'
    }
  } catch (err) {
    errorMsg.value = 'Đã xảy ra lỗi khi vào chế độ khách.'
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
      localStorage.setItem('token', data.token)
      localStorage.removeItem('guest_token')
      emit('auth-success', data.user)
    } else {
      errorMsg.value = data.error || 'Đăng nhập Google thất bại'
    }
  } catch (err) {
    errorMsg.value = 'Đã xảy ra lỗi khi đăng nhập Google.'
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
    <p class="auth-tagline font-label">LUYỆN ĐỀ THI THỬ · PHONG CÁCH ARCADE</p>

    <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="auth-cabinet">
      <div class="auth-inner">
        <div class="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'login'"
            class="auth-tab font-label"
            :class="{ 'auth-tab--active': mode === 'login' }"
            @click="switchMode('login')"
          >
            ĐĂNG NHẬP
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'signup'"
            class="auth-tab font-label"
            :class="{ 'auth-tab--active': mode === 'signup' }"
            @click="switchMode('signup')"
          >
            ĐĂNG KÝ
          </button>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit">
          <div v-if="errorMsg" class="auth-error font-label">{{ errorMsg }}</div>

          <div v-if="mode === 'signup'" class="arcade-field">
            <label class="arcade-label" for="auth-username">TÊN NGƯỜI DÙNG</label>
            <input id="auth-username" v-model="username" type="text" required class="arcade-input" />
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="auth-email">EMAIL</label>
            <input id="auth-email" v-model="email" type="email" required class="arcade-input" />
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="auth-password">MẬT KHẨU</label>
            <input id="auth-password" v-model="password" type="password" required class="arcade-input" />
          </div>

          <button type="submit" class="btn-arcade font-label" :disabled="isLoading">
            {{
              isLoading
                ? mode === 'login'
                  ? 'ĐANG ĐĂNG NHẬP…'
                  : 'ĐANG TẠO TÀI KHOẢN…'
                : mode === 'login'
                  ? 'ĐĂNG NHẬP'
                  : 'TẠO TÀI KHOẢN'
            }}
          </button>
        </form>

        <div class="auth-divider font-label">
          <span class="auth-divider-line" />
          <span>HOẶC</span>
          <span class="auth-divider-line" />
        </div>

        <div ref="googleBtnRef" class="auth-google"></div>

        <button type="button" class="btn-guest font-label" :disabled="isLoading" @click="handleGuestLogin">
          TIẾP TỤC KHÔNG CẦN TÀI KHOẢN
        </button>
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
  padding: 24px;
  overflow-y: auto;
}
.auth-wordmark {
  font-size: 22px;
  color: var(--amber);
  letter-spacing: 1px;
}
.auth-cursor {
  margin-left: 4px;
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
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.5px;
  margin: 8px 0 20px;
  text-align: center;
}
.auth-cabinet {
  width: 100%;
  max-width: 380px;
}
.auth-inner {
  padding: 20px;
}
.auth-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 20px;
}
.auth-tab {
  flex: 1;
  padding: 10px;
  font-size: 12px;
  letter-spacing: 0.5px;
  background: var(--cabinet-light);
  color: var(--muted);
  border: none;
  cursor: pointer;
}
.auth-tab--active {
  background: var(--amber);
  color: var(--ink);
}
.auth-tab:hover:not(.auth-tab--active) {
  color: var(--phosphor);
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.auth-error {
  color: var(--red);
  font-size: 12px;
  background: var(--ink);
  border-left: 3px solid var(--red);
  padding: 10px 12px;
}
.btn-arcade {
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  background: var(--green);
  color: var(--ink);
  border: none;
  padding: 14px;
  cursor: pointer;
  box-shadow: 0 4px 0 var(--green-shadow);
  margin-top: 6px;
}
.btn-arcade:active:not(:disabled) {
  transform: translateY(4px);
  box-shadow: none;
}
.btn-arcade:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.auth-divider {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 18px 0 14px;
  color: var(--muted);
  font-size: 11px;
}
.auth-divider-line {
  flex: 1;
  height: 1px;
  background: var(--cabinet-light);
}
.auth-google {
  margin-bottom: 12px;
}
.btn-guest {
  width: 100%;
  background: transparent;
  border: 2px solid var(--cabinet-light);
  color: var(--muted);
  padding: 12px;
  font-size: 11px;
  letter-spacing: 1px;
  cursor: pointer;
}
.btn-guest:hover:not(:disabled) {
  border-color: var(--amber);
  color: var(--phosphor);
}
.btn-guest:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.auth-tab:focus-visible,
.btn-arcade:focus-visible,
.btn-guest:focus-visible {
  outline: 2px solid var(--amber);
  outline-offset: 2px;
}
</style>
