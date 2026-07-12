<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { apiFetch } from '../utils/api';

interface Deck {
  _id: string;
  name: string;
  description: string;
}

const decks = ref<Deck[]>([]);
const isLoading = ref(true);
const isEditing = ref(false);
const editingDeckId = ref<string | null>(null);

const form = ref({
  name: '',
  description: ''
});

const fetchDecks = async () => {
  isLoading.value = true;
  try {
    const res = await apiFetch('/api/decks');
    decks.value = await res.json();
  } catch (error) {
    console.error('Failed to fetch decks:', error);
  } finally {
    isLoading.value = false;
  }
};

const saveDeck = async () => {
  try {
    if (isEditing.value && editingDeckId.value) {
      await apiFetch(`/api/decks/${editingDeckId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value)
      });
    } else {
      await apiFetch('/api/decks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value)
      });
    }
    
    form.value = { name: '', description: '' };
    isEditing.value = false;
    editingDeckId.value = null;
    await fetchDecks();
  } catch (error) {
    console.error('Failed to save deck:', error);
  }
};

const editDeck = (deck: Deck) => {
  form.value = { name: deck.name, description: deck.description || '' };
  isEditing.value = true;
  editingDeckId.value = deck._id;
};

const deleteDeck = async (id: string) => {
  if (!confirm('Are you sure you want to delete this deck?')) return;
  try {
    await apiFetch(`/api/decks/${id}`, { method: 'DELETE' });
    await fetchDecks();
  } catch (error) {
    console.error('Failed to delete deck:', error);
  }
};

const cancelEdit = () => {
  form.value = { name: '', description: '' };
  isEditing.value = false;
  editingDeckId.value = null;
};

onMounted(() => {
  fetchDecks();
});
</script>

<template>
  <div class="flex flex-col h-full bg-slate-900 text-slate-100 overflow-y-auto w-full p-4 md:p-8">
    <div class="max-w-4xl w-full mx-auto">
      
      <div class="flex justify-between items-center mb-8">
        <h2 class="text-3xl font-bold text-emerald-400">Manage Decks</h2>
      </div>

      <div class="bg-slate-800 p-6 rounded-2xl border border-slate-700 mb-8 shadow-lg">
        <h3 class="text-xl font-semibold mb-4 text-emerald-300">
          {{ isEditing ? 'Edit Deck' : 'Create New Deck' }}
        </h3>
        <form @submit.prevent="saveDeck" class="flex flex-col gap-4">
          <div>
            <label class="block text-sm text-slate-400 mb-1">Deck Name</label>
            <input 
              v-model="form.name" 
              required 
              type="text"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-100 focus:border-emerald-500 focus:outline-none transition-colors"
              placeholder="e.g. Spanish Vocabulary"
            />
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">Description (optional)</label>
            <input 
              v-model="form.description" 
              type="text"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-100 focus:border-emerald-500 focus:outline-none transition-colors"
              placeholder="e.g. Top 1000 common words"
            />
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
              {{ isEditing ? 'Update Deck' : 'Add Deck' }}
            </button>
          </div>
        </form>
      </div>

      <div class="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden shadow-lg">
        <div class="p-6 border-b border-slate-700 flex justify-between items-center">
          <h3 class="text-xl font-semibold text-slate-200">Your Decks</h3>
          <span class="text-sm text-slate-400" v-if="!isLoading">{{ decks.length }} total</span>
        </div>
        
        <div v-if="isLoading" class="p-8 text-center text-slate-400 animate-pulse">
          Loading decks...
        </div>
        
        <div v-else-if="decks.length === 0" class="p-8 text-center text-slate-500">
          No decks found. Create your first deck above!
        </div>
        
        <ul v-else class="divide-y divide-slate-700/50">
          <li v-for="deck in decks" :key="deck._id" class="p-4 sm:p-6 hover:bg-slate-700/30 transition-colors flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div class="flex-1 min-w-0">
              <div class="text-lg font-semibold text-slate-200 mb-1">{{ deck.name }}</div>
              <div class="text-sm text-slate-400">{{ deck.description }}</div>
            </div>
            
            <div class="flex gap-2 w-full sm:w-auto justify-end">
              <button 
                @click="editDeck(deck)" 
                class="px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 rounded-md transition-colors cursor-pointer"
              >
                Edit
              </button>
              <button 
                @click="deleteDeck(deck._id)" 
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
