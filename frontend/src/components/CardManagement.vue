<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { apiFetch } from '../utils/api';
import MarkdownRenderer from './MarkdownRenderer.vue';

interface Card {
  _id: string;
  front: string;
  back: string;
}

const cards = ref<Card[]>([]);
const decks = ref<any[]>([]);
const isLoading = ref(true);
const isEditing = ref(false);
const editingCardId = ref<string | null>(null);

const form = ref({
  front: '',
  back: '',
  deckId: ''
});

const emit = defineEmits(['close']);

const fetchCardsAndDecks = async () => {
  isLoading.value = true;
  try {
    const [cardsRes, decksRes] = await Promise.all([
      apiFetch('/api/cards'),
      apiFetch('/api/decks')
    ]);
    cards.value = await cardsRes.json();
    decks.value = await decksRes.json();
  } catch (error) {
    console.error('Failed to fetch data:', error);
  } finally {
    isLoading.value = false;
  }
};

const saveCard = async () => {
  try {
    if (isEditing.value && editingCardId.value) {
      await apiFetch(`/api/cards/${editingCardId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value)
      });
    } else {
      await apiFetch('/api/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value)
      });
    }
    
    // Reset form
    form.value = { front: '', back: '', deckId: '' };
    isEditing.value = false;
    editingCardId.value = null;
    
    // Refresh list
    await fetchCardsAndDecks();
  } catch (error) {
    console.error('Failed to save card:', error);
  }
};

const editCard = (card: any) => {
  form.value = { front: card.front, back: card.back, deckId: card.deckId || '' };
  isEditing.value = true;
  editingCardId.value = card._id;
};

const deleteCard = async (id: string) => {
  if (!confirm('Are you sure you want to delete this card?')) return;
  try {
    await apiFetch(`/api/cards/${id}`, { method: 'DELETE' });
    await fetchCardsAndDecks();
  } catch (error) {
    console.error('Failed to delete card:', error);
  }
};

const cancelEdit = () => {
  form.value = { front: '', back: '', deckId: '' };
  isEditing.value = false;
  editingCardId.value = null;
};

onMounted(() => {
  fetchCardsAndDecks();
});
</script>

<template>
  <div class="flex flex-col h-full bg-slate-900 text-slate-100 overflow-y-auto w-full p-4 md:p-8">
    <div class="max-w-4xl w-full mx-auto">
      
      <!-- Header -->
      <div class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold text-emerald-400">Manage Cards</h2>
        <button @click="emit('close')" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors cursor-pointer">
          Back to Study
        </button>
      </div>

      <!-- Add / Edit Form -->
      <div class="bg-slate-800 p-6 rounded-2xl border border-slate-700 mb-8 shadow-lg">
        <h3 class="text-xl font-semibold mb-4 text-emerald-300">
          {{ isEditing ? 'Edit Card' : 'Create New Card' }}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <form @submit.prevent="saveCard" class="flex flex-col gap-4">
            <div>
              <label class="block text-sm text-slate-400 mb-1">Deck (Optional)</label>
              <select 
                v-model="form.deckId"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-100 focus:border-emerald-500 focus:outline-none transition-colors"
              >
                <option value="">No Deck (Global)</option>
                <option v-for="deck in decks" :key="deck._id" :value="deck._id">
                  {{ deck.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm text-slate-400 mb-1">Front (Markdown supported)</label>
              <textarea 
                v-model="form.front" 
                required 
                rows="4"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-100 focus:border-emerald-500 focus:outline-none transition-colors resize-y"
                placeholder="e.g. What is the capital of France?"
              ></textarea>
            </div>
            <div>
              <label class="block text-sm text-slate-400 mb-1">Back (Markdown supported)</label>
              <textarea 
                v-model="form.back" 
                required 
                rows="4"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-100 focus:border-emerald-500 focus:outline-none transition-colors resize-y"
                placeholder="e.g. **Paris**"
              ></textarea>
            </div>
            <div class="flex gap-2 justify-end mt-2">
              <button 
                v-if="isEditing" 
                type="button" 
                @click="cancelEdit"
                class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button 
                type="submit"
                class="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors cursor-pointer"
              >
                {{ isEditing ? 'Update Card' : 'Add Card' }}
              </button>
            </div>
          </form>

          <!-- Markdown Preview -->
          <div class="bg-slate-900/50 rounded-lg p-4 border border-slate-700 flex flex-col gap-4">
            <h4 class="text-sm uppercase tracking-widest text-slate-500 font-semibold mb-2">Live Preview</h4>
            <div class="flex-1 bg-slate-800 rounded-xl p-4 border border-slate-700 overflow-y-auto">
              <div class="text-xs text-slate-500 mb-2">FRONT</div>
              <div class="text-lg text-slate-200 min-h-[3rem]">
                <MarkdownRenderer v-if="form.front" :content="form.front" />
                <span v-else class="text-slate-600 italic">Front preview...</span>
              </div>
              <hr class="border-slate-700 my-4">
              <div class="text-xs text-emerald-500/70 mb-2">BACK</div>
              <div class="text-lg text-slate-300 min-h-[3rem]">
                <MarkdownRenderer v-if="form.back" :content="form.back" />
                <span v-else class="text-slate-600 italic">Back preview...</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Card List -->
      <div class="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-lg">
        <div class="p-6 border-b border-slate-700 flex justify-between items-center">
          <h3 class="text-xl font-semibold text-slate-200">Your Cards</h3>
          <span class="text-sm text-slate-400" v-if="!isLoading">{{ cards.length }} total</span>
        </div>
        
        <div v-if="isLoading" class="p-8 text-center text-slate-400 animate-pulse">
          Loading cards...
        </div>
        
        <div v-else-if="cards.length === 0" class="p-8 text-center text-slate-500">
          No cards found. Create your first card above!
        </div>
        
        <ul v-else class="divide-y divide-slate-700/50">
          <li v-for="card in cards" :key="card._id" class="p-4 sm:p-6 hover:bg-slate-700/30 transition-colors flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div class="flex-1 min-w-0">
              <div class="text-sm text-slate-400 mb-1 uppercase tracking-wider font-semibold text-xs">Front</div>
              <div class="truncate text-slate-200 mb-3">{{ card.front }}</div>
              
              <div class="text-sm text-emerald-500/70 mb-1 uppercase tracking-wider font-semibold text-xs">Back</div>
              <div class="truncate text-slate-300">{{ card.back }}</div>
            </div>
            
            <div class="flex gap-2 w-full sm:w-auto justify-end">
              <button 
                @click="editCard(card)" 
                class="px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 rounded-md transition-colors cursor-pointer"
              >
                Edit
              </button>
              <button 
                @click="deleteCard(card._id)" 
                class="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded-md transition-colors cursor-pointer"
              >
                Delete
              </button>
            </div>
          </li>
        </ul>
      </div>

    </div>
  </div>
</template>
