import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '@/features/auth/store/authStore';

/**
 * Every top-level screen is a route. Routes are lazy-loaded so the exam
 * simulator and deck/card management aren't in the initial bundle — only
 * `AuthView` is eagerly reachable on a cold, logged-out load.
 *
 * `meta.public` marks the routes reachable without a token; everything else
 * goes through the `beforeEach` guard below.
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/auth',
    name: 'auth',
    component: () => import('@/features/auth/AuthView.vue'),
    meta: { public: true, fullBleed: true },
  },
  {
    path: '/',
    redirect: { name: 'dashboard' },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/features/dashboard/DashboardView.vue'),
  },
  {
    path: '/flashcards',
    name: 'flashcards',
    component: () => import('@/features/flashcards/FlashcardsView.vue'),
    meta: { fullBleed: true },
  },
  {
    path: '/flashcards/learn/:deckId',
    name: 'learn',
    component: () => import('@/features/flashcards/LearnView.vue'),
    props: true,
  },
  {
    path: '/flashcards/match/:deckId',
    name: 'match',
    component: () => import('@/features/flashcards/MatchView.vue'),
    props: true,
  },
  {
    path: '/decks',
    name: 'decks',
    component: () => import('@/features/library/DeckManagementView.vue'),
    meta: { fullBleed: true },
  },
  // Declared BEFORE the dynamic record so it always wins the match.
  {
    path: '/decks/unfiled',
    name: 'deck-unfiled',
    component: () => import('@/features/library/DeckDetailView.vue'),
    props: () => ({ deckId: null }),
    meta: { fullBleed: true },
  },
  {
    path: '/decks/:deckId',
    name: 'deck-detail',
    component: () => import('@/features/library/DeckDetailView.vue'),
    props: true,
    meta: { fullBleed: true },
  },
  // Retired in favour of the deck workspace.
  {
    path: '/cards',
    redirect: { name: 'decks' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/features/profile/ProfileView.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/features/profile/SettingsView.vue'),
  },
  {
    path: '/questions',
    name: 'question-bank',
    component: () => import('@/features/question-bank/QuestionBankView.vue'),
    meta: { fullBleed: true },
  },
  {
    path: '/exams',
    name: 'exams',
    component: () => import('@/features/exam/ExamHubView.vue'),
    meta: { fullBleed: true },
  },
  {
    path: '/exams/create',
    name: 'exam-create',
    component: () => import('@/features/exam/ExamComposerView.vue'),
    meta: { fullBleed: true },
  },
  {
    path: '/exams/:templateId/edit',
    name: 'exam-edit',
    component: () => import('@/features/exam/ExamComposerView.vue'),
    props: true,
    meta: { fullBleed: true },
  },
  {
    path: '/exams/session/:templateId',
    name: 'exam-session',
    component: () => import('@/features/exam/ExamView.vue'),
    props: true,
    meta: { fullBleed: true },
  },
  {
    path: '/exams/results/:sessionId',
    name: 'exam-results',
    component: () => import('@/features/exam/ExamResultsView.vue'),
    props: true,
    meta: { fullBleed: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: 'dashboard' },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();

  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'auth' };
  }
  // Already signed in? `/auth` has nothing to offer — bounce to the dashboard.
  if (to.name === 'auth' && auth.isAuthenticated) {
    return { name: 'dashboard' };
  }
  return true;
});
