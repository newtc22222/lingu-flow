<script setup lang="ts">
/**
 * Reusable pixel-notch cabinet border (the `.px` / `.px-frame` pattern from
 * the approved arcade mockup). Renders a clipped outer "frame" ring behind
 * an inner surface — the frame's corners are cut into an 8-bit notch shape,
 * and the inner surface inherits the same clip because it's nested inside.
 *
 * Padding/layout of the actual content is left to the caller (nest your own
 * flex/padding wrapper inside the default slot), so PixelFrame stays a pure
 * border primitive reusable across cards, panels, and HUD elements.
 */
withDefaults(
  defineProps<{
    /** Color of the outer notch ring. */
    frameColor?: 'amber' | 'cabinet-light'
    /** Color of the inner surface the content sits on. */
    surface?: 'cabinet' | 'ink'
    /** Thickness of the visible ring, in pixels. */
    ringWidth?: number
  }>(),
  {
    frameColor: 'amber',
    surface: 'cabinet',
    ringWidth: 3,
  },
)
</script>

<template>
  <div
    class="pixel-frame"
    :class="frameColor === 'amber' ? 'bg-amber' : 'bg-cabinet-light'"
    :style="{ padding: `${ringWidth}px` }"
  >
    <div class="h-full" :class="surface === 'ink' ? 'bg-ink' : 'bg-cabinet'">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.pixel-frame {
  --notch: var(--pixel-notch);
  clip-path: polygon(
    0 var(--notch),
    var(--notch) var(--notch),
    var(--notch) 0,
    calc(100% - var(--notch)) 0,
    calc(100% - var(--notch)) var(--notch),
    100% var(--notch),
    100% calc(100% - var(--notch)),
    calc(100% - var(--notch)) calc(100% - var(--notch)),
    calc(100% - var(--notch)) 100%,
    var(--notch) 100%,
    var(--notch) calc(100% - var(--notch)),
    0 calc(100% - var(--notch))
  );
}
</style>
