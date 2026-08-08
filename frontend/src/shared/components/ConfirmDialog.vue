<script setup lang="ts">
/**
 * Two-button confirm prompt. Chrome (overlay, frame, Escape, scroll lock,
 * focus trap) comes from ModalShell — this component is just the message and
 * the two actions.
 */
import { useI18n } from 'vue-i18n';
import ModalShell from './ModalShell.vue';
import AppButton from './AppButton.vue';

const { t } = useI18n();

withDefaults(
  defineProps<{
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'primary' | 'danger';
  }>(),
  {
    confirmText: '',
    cancelText: '',
    variant: 'danger',
  },
);

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void;
  (e: 'confirm'): void;
  (e: 'cancel'): void;
}>();

function handleCancel() {
  emit('update:isOpen', false);
  emit('cancel');
}

function handleConfirm() {
  emit('update:isOpen', false);
  emit('confirm');
}
</script>

<template>
  <ModalShell :is-open="isOpen" :title="title" :variant="variant" @close="handleCancel">
    <p class="confirm-message font-body">{{ message }}</p>

    <template #footer>
      <AppButton variant="secondary" class="confirm-btn" @click="handleCancel">
        {{ cancelText || t('common.cancel') }}
      </AppButton>
      <AppButton :variant="variant" class="confirm-btn" @click="handleConfirm">
        {{ confirmText || (variant === 'danger' ? t('common.delete') : t('common.save')) }}
      </AppButton>
    </template>
  </ModalShell>
</template>

<style scoped>
.confirm-message {
  color: var(--text-primary);
  font-size: var(--font-size-md);
  line-height: 1.6;
  margin: 0;
}

.confirm-btn {
  min-width: 100px;
}
</style>
