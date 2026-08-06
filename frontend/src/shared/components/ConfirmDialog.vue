<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import PixelFrame from './PixelFrame.vue'
import AppButton from './AppButton.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    isOpen: boolean
    title: string
    message: string
    confirmText?: string
    cancelText?: string
    variant?: 'primary' | 'danger'
  }>(),
  {
    confirmText: '',
    cancelText: '',
    variant: 'danger',
  }
)

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function handleCancel() {
  emit('update:isOpen', false)
  emit('cancel')
}

function handleConfirm() {
  emit('update:isOpen', false)
  emit('confirm')
}

function handleKeydown(event: KeyboardEvent) {
  if (props.isOpen && event.key === 'Escape') {
    handleCancel()
  }
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
)

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="confirm-overlay"
      role="dialog"
      aria-modal="true"
      :aria-label="title"
      @click.self="handleCancel"
    >
      <PixelFrame
        :frame-color="variant === 'danger' ? 'red' : 'amber'"
        surface="cabinet"
        :ring-width="3"
        class="confirm-card"
      >
        <div class="confirm-inner">
          <header class="confirm-header font-label">
            <h3 class="confirm-title font-pixel">{{ title }}</h3>
          </header>

          <p class="confirm-message font-body">{{ message }}</p>

          <footer class="confirm-actions">
            <AppButton variant="secondary" class="confirm-btn" @click="handleCancel">
              {{ cancelText || t('common.cancel') }}
            </AppButton>
            <AppButton
              :variant="variant"
              class="confirm-btn"
              @click="handleConfirm"
            >
              {{ confirmText || (variant === 'danger' ? t('common.delete') : t('common.save')) }}
            </AppButton>
          </footer>
        </div>
      </PixelFrame>
    </div>
  </ Teleport>
</template>

<style scoped>
/* stylelint-disable-next-line function-disallowed-list -- semi-transparent modal backdrop overlay */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 12, 18, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  z-index: 100;
  backdrop-filter: blur(4px);
}

.confirm-card {
  width: 100%;
  max-width: 420px;
  box-shadow: 0 12px 32px var(--ink);
}

.confirm-inner {
  padding: var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}

.confirm-header {
  border-bottom: 1px solid var(--surface-panel-border);
  padding-bottom: var(--space-4);
}

.confirm-title {
  font-size: var(--font-size-md);
  color: var(--color-accent);
  letter-spacing: var(--tracking-tight);
}

.confirm-message {
  color: var(--text-primary);
  font-size: var(--font-size-md);
  line-height: 1.6;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-5);
  margin-top: var(--space-3);
}

.confirm-btn {
  min-width: 100px;
}
</style>
