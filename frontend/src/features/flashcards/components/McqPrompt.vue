<script setup lang="ts">
/** Multiple-choice prompt for Learn mode's first round. */
import AppButton from '@/shared/components/AppButton.vue';

defineProps<{
  prompt: string;
  options: string[];
  /** Set once the user has answered; drives the correct/incorrect styling. */
  selected: string | null;
  correctAnswer: string;
  disabled: boolean;
}>();

defineEmits<{
  (e: 'select', option: string): void;
}>();
</script>

<template>
  <div class="mcq">
    <p class="mcq-prompt font-body">{{ prompt }}</p>

    <div class="mcq-options">
      <AppButton
        v-for="option in options"
        :key="option"
        :variant="
          selected === null
            ? 'secondary'
            : option === correctAnswer
              ? 'primary'
              : option === selected
                ? 'danger'
                : 'secondary'
        "
        class="mcq-option"
        :disabled="disabled"
        @click="$emit('select', option)"
      >
        {{ option }}
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.mcq-prompt {
  font-size: var(--font-size-xl);
  color: var(--text-primary);
  text-align: center;
  margin: 0 0 var(--space-10);
}
.mcq-options {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-5);
}
@media (min-width: 640px) {
  .mcq-options {
    grid-template-columns: 1fr 1fr;
  }
}
.mcq-option {
  width: 100%;
}
</style>
