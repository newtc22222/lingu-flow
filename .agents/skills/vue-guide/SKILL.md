---
name: vue-guide
description: Conventions, patterns, and best practices for Vue 3 Composition API, TypeScript, Pinia, and the arcade pixel design system in LinguFlow frontend.
---

# Vue 3 & Frontend Skill Guide

This skill provides guidelines and patterns for developing Vue 3 components in the `frontend/` directory.

## Core Rules & Architecture

1. **Composition API Only**
   - All Vue components MUST use `<script setup lang="ts">`.
   - Never use Options API (`data`, `methods`, `computed` option objects).

2. **Folder structure — feature folders, mid-migration**
   - New/actively-developed UI lives under `frontend/src/features/<domain>/` (e.g. `features/auth`, `features/dashboard`, `features/exam`, `features/flashcards`, `features/library`), each holding its top-level `<Name>View.vue`, a `components/` subfolder for domain-local pieces, and optionally a `store/` for Pinia stores (e.g. `features/exam/store/examStore.ts`).
   - Cross-feature reusable primitives go in `frontend/src/shared/components/` (e.g. `PixelFrame.vue`).
   - The old flat `frontend/src/components/` folder is legacy: some files there are still live and imported (`ExamHub.vue`, `ExamResults.vue`, `ExamCreator.vue`, `MarkdownRenderer.vue`), others are orphaned dead code (`StudyDashboard.vue`, `HelloWorld.vue` — not imported by `App.vue` anymore). Check `App.vue`'s imports, not just grep hits, before assuming a `components/*.vue` file is a real call site.
   - Path alias `@` maps to `frontend/src` (see `vite.config.ts` / `tsconfig.app.json`) — prefer `@/...` imports for new code under `features/`.

3. **API Communication**
   - Use relative `/api/...` endpoints (proxied by Vite to FastAPI on port 8000 during dev).
   - Use `apiFetch` from `src/utils/api.ts` for authenticated requests (it automatically attaches `Authorization: Bearer <token>` and handles 401 token invalidation). Shared/cross-view data flows go through a Pinia store action that itself calls `apiFetch` (see `examStore.ts`) rather than calling `apiFetch` directly from multiple components.

4. **State management**
   - Local, single-view state: plain `ref`/`computed` in the component.
   - State shared across components or views, or with non-trivial async lifecycle (timers, in-flight request tracking): a Pinia store (`defineStore` with the setup-function form, see `features/exam/store/examStore.ts`). Pinia is installed globally via `createPinia()` in `main.ts`.

5. **Styling & Design System — retro-arcade pixel theme, NOT slate/emerald**
   - Tailwind CSS v4, but the palette is a bespoke 8-color arcade token set, not a generic Tailwind palette: `ink`, `cabinet`, `cabinet-light`, `amber`, `red`, `green`, `phosphor`, `muted` (plus derived shades like `amber-light`, `surface-hover`). These are defined as CSS custom properties in `frontend/src/styles/tokens.css` and re-exposed as Tailwind utilities through a `@theme` block, so use them as ordinary Tailwind classes: `bg-ink`, `text-phosphor`, `bg-amber`, `border-cabinet-light`, etc. Never hardcode a hex value in a component — if a color isn't already a token, that's a design decision to raise, not something to invent inline.
   - Typography: `font-pixel` (Press Start 2P) for chunky pixel headers/short labels only, `font-body` (IBM Plex Sans) for prose, `font-label` (IBM Plex Mono) for short uppercase UI labels. **`font-pixel` has no Vietnamese diacritic glyphs** — any string that may contain Vietnamese text must use `font-body` or `font-label`, never `font-pixel`.
   - Reusable low-level visual patterns (the pixel-notch border, shared form-field styling) are global utility classes/components rather than re-implemented scoped CSS per component once more than one consumer needs them — see `.arcade-field`/`.arcade-label`/`.arcade-input` in `tokens.css` and `shared/components/PixelFrame.vue`.

6. **Component State & Navigation**
   - Current top-level view navigation uses string unions (`AppView` type in `src/App.vue`) — there is no router library.

7. **Markdown rendering**
   - Use the existing `MarkdownRenderer.vue` (`marked` + `dompurify`) for any user-facing markdown content instead of introducing a second markdown pipeline.

## Component Template

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'

const props = defineProps<{
  title?: string
}>()

const emit = defineEmits<{
  (e: 'navigate', view: string): void
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const dataList = ref<Array<{ id: number; name: string }>>([])

const itemCount = computed(() => dataList.value.length)

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await apiFetch('/api/example')
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
    dataList.value = await res.json()
  } catch (err: any) {
    error.value = err.message || 'Failed to fetch data'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="p-6 text-phosphor bg-ink min-h-screen">
    <h1 class="font-label text-2xl font-bold text-amber mb-4">{{ title || 'Overview' }}</h1>

    <div v-if="loading" class="text-muted animate-pulse font-body">
      Loading...
    </div>

    <div v-else-if="error" class="p-4 bg-red/10 border border-red rounded text-red font-body">
      {{ error }}
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="item in dataList"
        :key="item.id"
        class="p-3 bg-cabinet rounded border border-cabinet-light hover:border-amber/50 transition-colors font-body"
      >
        {{ item.name }}
      </div>
    </div>
  </div>
</template>
```
