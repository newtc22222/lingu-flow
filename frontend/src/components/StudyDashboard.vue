<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import MarkdownRenderer from './MarkdownRenderer.vue';

interface Card {
  _id: string;
  front: string;
  back: string;
  srsData: any;
}

const cards = ref<Card[]>([]);
const currentCardIndex = ref(0);
const isFlipped = ref(false);
const isLoading = ref(true);
const message = ref('');

const currentCard = computed(() => cards.value[currentCardIndex.value] || null);
import { apiFetch } from '../utils/api';
import { computed } from 'vue';

const fetchCards = async () => {
  isLoading.value = true;
  try {
    const res = await apiFetch('/api/cards/study');
    cards.value = await res.json();
  } catch (error) {
    console.error('Failed to fetch cards:', error);
  } finally {
    isLoading.value = false;
  }
};

const handleReview = async (score: number) => {
  if (!currentCard.value) return;

  try {
    await apiFetch(`/api/cards/review/${currentCard.value._id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score }),
    });

    // Move to next card
    isFlipped.value = false;
    currentCardIndex.value++;
  } catch (error) {
    console.error('Failed to submit review:', error);
  }
};

const onKeyDown = (e: KeyboardEvent) => {
  // Ignore if user is typing in an input
  if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;

  if (e.code === 'Space') {
    e.preventDefault();
    if (currentCard.value) {
      isFlipped.value = !isFlipped.value;
    }
  } else if (isFlipped.value) {
    switch (e.key) {
      case '1': handleReview(1); break; // Blackout
      case '2': handleReview(2); break; // Hard
      case '3': handleReview(3); break; // Good
      case '4': handleReview(4); break; // Easy
    }
  }
};

let eventSource: EventSource | null = null;

onMounted(() => {
  fetchCards();
  window.addEventListener('keydown', onKeyDown);

  eventSource = new EventSource('/api/events');
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.message) {
      message.value = data.message;
      // Clear message after 3 seconds
      setTimeout(() => message.value = '', 3000);
    }
  };
});

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown);
  if (eventSource) {
    eventSource.close();
  }
});
</script>

<template>
  <div class="flex flex-col items-center justify-center h-full p-4 bg-slate-900 text-slate-100 relative">
    <!-- Remaining count badge floating -->
    <div class="absolute top-4 right-4 z-10">
      <span class="text-sm bg-slate-700 px-3 py-1 rounded-full text-slate-300 shadow-md">
        Remaining: {{ cards.length - currentCardIndex }}
      </span>
    </div>

    <!-- SSE Notification -->
    <div 
      v-if="message" 
      class="absolute top-20 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-4 py-2 rounded-lg transition-all duration-300 shadow-lg shadow-emerald-500/10"
    >
      {{ message }}
    </div>

    <!-- Main Content Area -->
    <div v-if="isLoading" class="text-slate-400 animate-pulse">Loading cards...</div>
    
    <div v-else-if="!currentCard" class="text-center p-8 bg-slate-800 rounded-2xl shadow-xl border border-slate-700">
      <h2 class="text-2xl font-semibold mb-2 text-emerald-400">All done! 🎉</h2>
      <p class="text-slate-400">You have reviewed all your cards for now.</p>
    </div>

    <div v-else class="w-full max-w-2xl perspective-1000">
      <!-- Flashcard -->
      <div 
        class="bg-slate-800 rounded-2xl p-8 min-h-[300px] flex flex-col items-center justify-center cursor-pointer transition-all duration-500 transform-style-3d shadow-2xl border border-slate-700 hover:border-slate-600"
        @click="isFlipped = !isFlipped"
      >
        <!-- Front side -->
        <div v-if="!isFlipped" class="w-full flex flex-col items-center animate-fade-in">
          <div class="text-xs uppercase tracking-widest text-slate-500 mb-6 font-semibold">Front</div>
          <div class="text-2xl lg:text-3xl font-medium text-center">
            <MarkdownRenderer :content="currentCard.front" />
          </div>
          <div class="mt-12 text-slate-500 text-sm opacity-50 flex items-center gap-2">
            <kbd class="px-2 py-1 bg-slate-700 rounded text-xs font-mono">Space</kbd> to flip
          </div>
        </div>

        <!-- Back side -->
        <div v-else class="w-full flex flex-col items-center animate-fade-in">
          <div class="text-xs uppercase tracking-widest text-emerald-500/70 mb-6 font-semibold">Back</div>
          <div class="text-xl lg:text-2xl text-center text-slate-300">
            <MarkdownRenderer :content="currentCard.back" />
          </div>
        </div>
      </div>

      <!-- Controls -->
      <div 
        class="mt-8 grid grid-cols-4 gap-4 transition-all duration-300"
        :class="isFlipped ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'"
      >
        <button @click="handleReview(1)" class="review-btn group hover:bg-rose-500/20 hover:border-rose-500/50 hover:text-rose-400">
          <span class="text-xs mb-1 opacity-50 group-hover:opacity-100">Blackout</span>
          <kbd class="px-2 py-1 bg-slate-800/50 rounded font-mono text-sm border border-slate-700 group-hover:border-rose-500/30">1</kbd>
        </button>
        <button @click="handleReview(2)" class="review-btn group hover:bg-orange-500/20 hover:border-orange-500/50 hover:text-orange-400">
          <span class="text-xs mb-1 opacity-50 group-hover:opacity-100">Hard</span>
          <kbd class="px-2 py-1 bg-slate-800/50 rounded font-mono text-sm border border-slate-700 group-hover:border-orange-500/30">2</kbd>
        </button>
        <button @click="handleReview(3)" class="review-btn group hover:bg-blue-500/20 hover:border-blue-500/50 hover:text-blue-400">
          <span class="text-xs mb-1 opacity-50 group-hover:opacity-100">Good</span>
          <kbd class="px-2 py-1 bg-slate-800/50 rounded font-mono text-sm border border-slate-700 group-hover:border-blue-500/30">3</kbd>
        </button>
        <button @click="handleReview(4)" class="review-btn group hover:bg-emerald-500/20 hover:border-emerald-500/50 hover:text-emerald-400">
          <span class="text-xs mb-1 opacity-50 group-hover:opacity-100">Easy</span>
          <kbd class="px-2 py-1 bg-slate-800/50 rounded font-mono text-sm border border-slate-700 group-hover:border-emerald-500/30">4</kbd>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@reference "tailwindcss";

.perspective-1000 {
  perspective: 1000px;
}
.transform-style-3d {
  transform-style: preserve-3d;
}
.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.review-btn {
  @apply flex flex-col items-center justify-center p-3 rounded-xl border border-slate-700 bg-slate-800 text-slate-400 transition-all duration-200;
}
</style>
