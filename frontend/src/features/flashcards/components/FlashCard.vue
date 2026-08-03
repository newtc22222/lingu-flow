<script setup lang="ts">
import PixelFrame from '@/shared/components/PixelFrame.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

withDefaults(
  defineProps<{
    front: string
    back: string
    flipped: boolean
    frontEyebrow?: string
    backEyebrow?: string
    hint?: string
  }>(),
  {
    frontEyebrow: '▸ THUẬT NGỮ',
    backEyebrow: '▸ ĐỊNH NGHĨA',
    hint: 'chạm để lật thẻ',
  },
)

const emit = defineEmits<{
  (e: 'toggle'): void
}>()
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
            <span class="fc-eyebrow font-label">{{ frontEyebrow }}</span>
            <div class="fc-term font-body"><MarkdownRenderer :content="front" /></div>
            <p class="fc-hint font-label">{{ hint }}</p>
          </div>
        </PixelFrame>
      </div>
      <div class="fc-face fc-back">
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="h-full w-full">
          <div class="fc-face-inner">
            <span class="fc-eyebrow font-label">{{ backEyebrow }}</span>
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
  margin: 0 auto 26px;
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
  outline: 2px solid var(--color-focus-ring);
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
  padding: 28px;
  text-align: center;
}
.fc-eyebrow {
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text-label-accent);
  margin-bottom: 16px;
}
.fc-term {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-primary);
}
.fc-def {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
}
.fc-hint {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 16px;
}

@media (prefers-reduced-motion: reduce) {
  .flip-card {
    transition: none;
  }
}
</style>
