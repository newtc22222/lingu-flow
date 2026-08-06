<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import MarkdownRenderer from '@/shared/components/MarkdownRenderer.vue'

const props = defineProps<{
  front: string
  back: string
  flipped: boolean
  frontEyebrow?: string
  backEyebrow?: string
  hint?: string
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
}>()

const { t } = useI18n()

// Labels default to the active locale rather than hardcoded Vietnamese, but
// stay overridable so Learn/Match can relabel the faces.
const resolvedFrontEyebrow = computed(() => props.frontEyebrow ?? `▸ ${t('deckDetail.term')}`)
const resolvedBackEyebrow = computed(() => props.backEyebrow ?? `▸ ${t('deckDetail.definition')}`)
const resolvedHint = computed(() => props.hint ?? t('flashcards.flipHint'))
</script>

<template>
  <div class="flip-zone">
    <div
      class="flip-card"
      :class="{ flipped }"
      role="button"
      tabindex="0"
      :aria-pressed="flipped"
      aria-label="Flashcard, press space or enter to flip"
      @click="emit('toggle')"
      @keydown.space.prevent="emit('toggle')"
      @keydown.enter.prevent="emit('toggle')"
    >
      <div class="fc-face fc-front">
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="h-full w-full">
          <div class="fc-face-inner">
            <span class="fc-eyebrow font-label">{{ resolvedFrontEyebrow }}</span>
            <div class="fc-term font-body"><MarkdownRenderer :content="front" /></div>
            <p class="fc-hint font-label">{{ resolvedHint }}</p>
          </div>
        </PixelFrame>
      </div>
      <div class="fc-face fc-back">
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="h-full w-full">
          <div class="fc-face-inner">
            <span class="fc-eyebrow font-label">{{ resolvedBackEyebrow }}</span>
            <div class="fc-def font-body"><MarkdownRenderer :content="back" /></div>
          </div>
        </PixelFrame>
      </div>
    </div>
  </div>
</template>

<style scoped>
.flip-zone {
  perspective: 1200px;
  max-width: 520px;
  margin: 0 auto var(--space-11);
  height: 280px;
}
.flip-card {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.5s;
  cursor: pointer;
}
.flip-card:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 4px;
}
.flip-card.flipped {
  transform: rotateY(180deg);
}
.fc-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
}
.fc-back {
  transform: rotateY(180deg);
}
.fc-face-inner {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - layout one-off, see design-tokens.json notes */
  padding: 28px;
  text-align: center;
}
.fc-eyebrow {
  font-weight: 700;
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--text-label-accent);
  margin-bottom: var(--space-8);
}
.fc-term {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-primary);
}
.fc-def {
  font-size: var(--font-size-lg);
  line-height: 1.6;
  color: var(--text-primary);
}
.fc-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-top: var(--space-8);
}

@media (prefers-reduced-motion: reduce) {
  .flip-card {
    transition: none;
  }
}
</style>
