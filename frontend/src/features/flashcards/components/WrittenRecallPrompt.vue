<script setup lang="ts">
/** Free-text recall prompt for Learn mode's second round. */
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '@/shared/components/AppButton.vue'

const props = defineProps<{
  prompt: string
  /** Null until the answer is checked, then the verdict for this attempt. */
  verdict: 'correct' | 'incorrect' | null
  correctAnswer: string
}>()

const emit = defineEmits<{
  (e: 'check', answer: string): void
  (e: 'next'): void
}>()

const { t } = useI18n()

const answer = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

// Each new prompt clears the box and takes focus, so the round can be played
// entirely from the keyboard.
watch(
  () => props.prompt,
  async () => {
    answer.value = ''
    await nextTick()
    inputRef.value?.focus()
  },
  { immediate: true },
)

function submit() {
  if (props.verdict === null) {
    emit('check', answer.value)
  } else {
    emit('next')
  }
}
</script>

<template>
  <form class="written" @submit.prevent="submit">
    <p class="written-prompt font-body">{{ prompt }}</p>

    <div class="arcade-field">
      <label class="arcade-label" for="written-answer">{{ t('learn.typeAnswer') }}</label>
      <input
        id="written-answer"
        ref="inputRef"
        v-model="answer"
        type="text"
        autocomplete="off"
        class="arcade-input"
        :readonly="verdict !== null"
      />
    </div>

    <p v-if="verdict === 'correct'" class="written-verdict written-verdict--ok font-label">
      {{ t('learn.correct') }}
    </p>
    <p v-else-if="verdict === 'incorrect'" class="written-verdict written-verdict--bad font-label">
      {{ t('learn.incorrect') }} — {{ t('learn.correctAnswerWas', { answer: correctAnswer }) }}
    </p>

    <AppButton type="submit" class="written-submit">
      {{ verdict === null ? t('learn.check') : t('learn.next') }}
    </AppButton>
  </form>
</template>

<style scoped>
.written {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}
.written-prompt {
  font-size: var(--font-size-xl);
  color: var(--text-primary);
  text-align: center;
  margin: 0;
}
.written-verdict {
  font-size: var(--font-size-md);
  margin: 0;
  text-align: center;
}
.written-verdict--ok {
  color: var(--status-success);
}
.written-verdict--bad {
  color: var(--status-danger);
}
.written-submit {
  align-self: center;
}
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
