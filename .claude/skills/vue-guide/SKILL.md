---
name: vue-guide
description: Conventions, patterns, and best practices for Vue 3 Composition API, TypeScript, Pinia, and the arcade pixel design system in LinguFlow's frontend. Use when creating or editing anything under frontend/src.
---

# Vue 3 & Frontend Skill Guide

This skill provides guidelines and patterns for developing Vue 3 components in the `frontend/` directory. It mirrors the `vue-guide` skill shipped in `.agents/skills/` for non-Claude tools — keep both in sync if either changes.

## Core Rules & Architecture

1. **Composition API only** — every component uses `<script setup lang="ts">`. Never Options API (`data`, `methods`, `computed` option objects).

2. **Folder structure — feature folders, mid-migration**
   - New/actively-developed UI lives under `frontend/src/features/<domain>/` (e.g. `features/auth`, `features/dashboard`, `features/exam`, `features/flashcards`, `features/library`): a top-level `<Name>View.vue`, a `components/` subfolder for domain-local pieces, and optionally `store/` for Pinia stores (e.g. `features/exam/store/examStore.ts`).
   - Cross-feature reusable primitives go in `frontend/src/shared/components/` (e.g. `PixelFrame.vue`).
   - The old flat `frontend/src/components/` folder is legacy: `ExamHub.vue`, `ExamResults.vue`, `ExamCreator.vue`, `MarkdownRenderer.vue` are still live and imported. `StudyDashboard.vue` and `HelloWorld.vue` are orphaned dead code (not imported by `App.vue` anymore, superseded by `features/dashboard/DashboardView.vue`) — don't treat a grep hit on them as a real call site; check `App.vue`'s actual imports.
   - Path alias `@` maps to `frontend/src` (`vite.config.ts` / `tsconfig.app.json`) — prefer `@/...` imports in new `features/` code.

3. **API communication**
   - Relative `/api/...` paths only (Vite proxies to FastAPI on `:8000` in dev) — never an absolute backend URL.
   - Use `apiFetch` from `src/utils/api.ts` for authenticated requests (attaches `Authorization: Bearer <token>`, clears token + reloads on 401). For state shared across views, put `apiFetch` calls inside a Pinia store action (see `examStore.ts`) rather than calling it from multiple components directly.

4. **State management**
   - Local, single-view state: plain `ref`/`computed`.
   - Cross-component/view state, or state with async lifecycle (timers, in-flight tracking): a Pinia store (`defineStore` setup-function form). Pinia is installed globally via `createPinia()` in `main.ts`.

5. **Styling — retro-arcade pixel theme, NOT slate/emerald**
   - Tailwind v4 with a bespoke 8-color token set (`ink`, `cabinet`, `cabinet-light`, `amber`, `red`, `green`, `phosphor`, `muted`, plus derived shades) defined in `frontend/src/styles/tokens.css` and exposed as Tailwind utilities via `@theme` (`bg-ink`, `text-phosphor`, `bg-amber`, `border-cabinet-light`, ...). Never hardcode a hex value — if a needed color isn't a token yet, that's a design decision to flag, not invent inline.
   - Fonts: `font-pixel` (Press Start 2P, headers/short labels only), `font-body` (IBM Plex Sans, prose), `font-label` (IBM Plex Mono, short uppercase UI labels). **`font-pixel` has no Vietnamese diacritic glyphs** — any string that may contain Vietnamese text must use `font-body`/`font-label`, never `font-pixel`.
   - Shared low-level visual patterns (pixel-notch border, form-field styling) are global utility classes/components once more than one consumer needs them (`.arcade-field`/`.arcade-label`/`.arcade-input` in `tokens.css`, `shared/components/PixelFrame.vue`) — don't reimplement per-component scoped CSS for these.

6. **Navigation** — no router library. `App.vue` holds a single `currentView` ref (`AppView` string union) and conditionally renders views.

7. **Markdown** — use the existing `MarkdownRenderer.vue` (`marked` + `dompurify`); don't add a second markdown pipeline.

## Component Template

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'

const props = defineProps<{ title?: string }>()

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

onMounted(fetchData)
</script>

<template>
  <div class="p-6 text-phosphor bg-ink min-h-screen">
    <h1 class="font-label text-2xl font-bold text-amber mb-4">{{ title || 'Overview' }}</h1>
    <div v-if="loading" class="text-muted animate-pulse font-body">Loading...</div>
    <div v-else-if="error" class="p-4 bg-red/10 border border-red rounded text-red font-body">{{ error }}</div>
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
