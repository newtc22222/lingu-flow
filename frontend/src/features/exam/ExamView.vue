<script setup lang="ts">
/**
 * Proctored exam booth.
 * Briefing loads template meta without creating a session; START calls store.start.
 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { apiFetch } from '@/utils/api';
import AppButton from '@/shared/components/AppButton.vue';
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import ExamHud from './components/ExamHud.vue';
import ExamAnswerSheet from './components/ExamAnswerSheet.vue';
import QuestionCard from './components/QuestionCard.vue';
import { useExamStore } from './store/examStore';

const props = defineProps<{ templateId: string }>();

const { t } = useI18n();
const router = useRouter();
const store = useExamStore();

type Gate = 'loading-brief' | 'briefing' | 'brief-error' | 'live';

const gate = ref<Gate>('loading-brief');
const briefError = ref('');
const briefMeta = ref<{
  name: string;
  examType: string;
  description: string;
  durationMinutes: number;
  totalQuestions: number;
  passingScore: number;
  level: string;
} | null>(null);

const showSubmitConfirm = ref(false);
const keyListenerAttached = ref(false);

const isLastQuestion = computed(() => store.currentIndex === store.questions.length - 1);
const isSubmitting = computed(() => store.phase === 'submitting');
const unansweredCount = computed(() => Math.max(0, store.questions.length - store.answeredCount));
const submitMessage = computed(() =>
  unansweredCount.value > 0
    ? t('exam.confirmSubmitPartial', { count: unansweredCount.value })
    : t('exam.confirmSubmitAll'),
);
const questionIds = computed(() => store.questions.map((q) => q.id));

async function loadBriefing() {
  gate.value = 'loading-brief';
  briefError.value = '';
  try {
    const res = await apiFetch(`/api/exams/templates/${props.templateId}`);
    if (!res.ok) throw new Error(t('exam.briefingLoadFailed'));
    const data = (await res.json()) as Record<string, unknown>;
    briefMeta.value = {
      name: (data.name as string) ?? '',
      examType: (data.examType as string) ?? 'custom',
      description: (data.description as string) ?? '',
      durationMinutes: (data.durationMinutes as number) ?? 60,
      totalQuestions: (data.totalQuestions as number) ?? 0,
      passingScore: (data.passingScore as number) ?? 60,
      level: (data.level as string) ?? '',
    };
    gate.value = 'briefing';
  } catch (err) {
    briefError.value = err instanceof Error ? err.message : t('exam.briefingLoadFailed');
    gate.value = 'brief-error';
  }
}

function attachKeys() {
  if (keyListenerAttached.value) return;
  window.addEventListener('keydown', onKeyDown);
  keyListenerAttached.value = true;
}
function detachKeys() {
  if (!keyListenerAttached.value) return;
  window.removeEventListener('keydown', onKeyDown);
  keyListenerAttached.value = false;
}

async function beginExam() {
  gate.value = 'live';
  await store.start(props.templateId);
  if (store.phase === 'in-progress') attachKeys();
}

function requestSubmit() {
  if (store.isLocked || store.phase !== 'in-progress') return;
  showSubmitConfirm.value = true;
}

function confirmSubmit() {
  void store.finish();
}

function handleCardNext() {
  if (isLastQuestion.value) {
    requestSubmit();
  } else {
    store.next();
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return;
  if ((e.target as HTMLElement).isContentEditable) return;
  if (e.isComposing || e.keyCode === 229) return;
  if (store.isLocked || store.phase !== 'in-progress') return;
  if (showSubmitConfirm.value) return;

  const key = e.key.toUpperCase();
  switch (key) {
    case 'A':
    case 'B':
    case 'C':
    case 'D':
      e.preventDefault();
      store.selectAnswer(key);
      break;
    case 'ENTER':
      e.preventDefault();
      if (isLastQuestion.value) requestSubmit();
      else store.next();
      break;
    case 'ARROWLEFT':
      e.preventDefault();
      store.previous();
      break;
    case 'ARROWRIGHT':
      e.preventDefault();
      store.next();
      break;
  }
}

watch(
  () => store.phase,
  (phase) => {
    if (phase === 'finished' && store.finishedSessionId) {
      detachKeys();
      void router.replace({
        name: 'exam-results',
        params: { sessionId: store.finishedSessionId },
      });
    }
    if (phase === 'in-progress') attachKeys();
    if (phase === 'error' || phase === 'submitting') detachKeys();
  },
);

watch(
  () => props.templateId,
  () => {
    store.teardown();
    detachKeys();
    void loadBriefing();
  },
);

onMounted(() => {
  void loadBriefing();
});

onUnmounted(() => {
  detachKeys();
  store.teardown();
});
</script>

<template>
  <div class="exam-booth">
    <!-- Briefing -->
    <template v-if="gate === 'loading-brief'">
      <p class="exam-status font-label">{{ t('exam.loadingExam') }}</p>
    </template>

    <template v-else-if="gate === 'brief-error'">
      <p class="exam-status exam-status--error font-body">{{ briefError }}</p>
      <div class="exam-status-actions">
        <AppButton variant="secondary" @click="router.push({ name: 'exams' })">
          {{ t('exam.backToLobby') }}
        </AppButton>
        <AppButton @click="loadBriefing">{{ t('exam.retry') }}</AppButton>
      </div>
    </template>

    <template v-else-if="gate === 'briefing' && briefMeta">
      <div class="briefing">
        <AppButton
          variant="secondary"
          class="briefing-back"
          @click="router.push({ name: 'exams' })"
        >
          {{ t('exam.backToLobby') }}
        </AppButton>

        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
          <div class="briefing-panel">
            <p class="briefing-eyebrow font-label">{{ t('exam.briefingTitle') }}</p>
            <h1 class="briefing-title font-body">{{ briefMeta.name }}</h1>
            <p v-if="briefMeta.description" class="briefing-desc font-body">
              {{ briefMeta.description }}
            </p>
            <p class="briefing-ready font-body">{{ t('exam.briefingReady') }}</p>

            <div class="briefing-stats">
              <div class="briefing-stat">
                <span class="briefing-stat-label font-label">{{ t('exam.briefingDuration') }}</span>
                <span class="briefing-stat-value font-label">
                  {{ briefMeta.durationMinutes }} {{ t('common.minutes') }}
                </span>
              </div>
              <div class="briefing-stat">
                <span class="briefing-stat-label font-label">{{
                  t('exam.briefingQuestions')
                }}</span>
                <span class="briefing-stat-value font-label">{{ briefMeta.totalQuestions }}</span>
              </div>
              <div class="briefing-stat">
                <span class="briefing-stat-label font-label">{{ t('exam.briefingPass') }}</span>
                <span class="briefing-stat-value font-label">{{ briefMeta.passingScore }}%</span>
              </div>
              <div v-if="briefMeta.level" class="briefing-stat">
                <span class="briefing-stat-label font-label">{{ briefMeta.examType }}</span>
                <span class="briefing-stat-value font-label">{{ briefMeta.level }}</span>
              </div>
            </div>

            <div class="briefing-keys">
              <span class="briefing-keys-title font-label">{{ t('exam.briefingKeys') }}</span>
              <span class="briefing-keys-hint font-body">{{ t('exam.briefingKeysHint') }}</span>
            </div>

            <AppButton class="briefing-start" @click="beginExam">
              {{ t('exam.startExam') }}
            </AppButton>
          </div>
        </PixelFrame>
      </div>
    </template>

    <!-- Live booth -->
    <template v-else-if="gate === 'live'">
      <template v-if="store.phase === 'loading'">
        <p class="exam-status font-label">{{ t('exam.loadingExam') }}</p>
      </template>

      <template v-else-if="store.phase === 'error'">
        <p class="exam-status exam-status--error font-body">
          {{ store.error ?? t('exam.loadFailed') }}
        </p>
        <div class="exam-status-actions">
          <AppButton variant="secondary" @click="router.push({ name: 'exams' })">
            {{ t('exam.backToLobby') }}
          </AppButton>
          <AppButton @click="beginExam">{{ t('exam.retry') }}</AppButton>
        </div>
      </template>

      <template v-else-if="store.phase === 'submitting'">
        <p class="exam-status font-label">{{ t('exam.submitting') }}</p>
      </template>

      <template v-else-if="store.currentQuestion">
        <ExamHud
          :title="store.examTitle"
          :can-submit="!store.isLocked"
          :is-submitting="isSubmitting"
          @submit="requestSubmit"
        />

        <QuestionCard
          :question="store.currentQuestion"
          :selected-answer="store.answers[store.currentQuestion.id]"
          :disabled="store.isLocked"
          :is-last-question="isLastQuestion"
          :current="store.currentIndex + 1"
          :total="store.questions.length"
          @select="store.selectAnswer"
          @submit="requestSubmit"
          @previous="store.previous"
          @next="handleCardNext"
        />

        <ExamAnswerSheet
          :total="store.questions.length"
          :current-index="store.currentIndex"
          :answers="store.answers"
          :question-ids="questionIds"
          :disabled="store.isLocked"
          @select="store.goToQuestion"
        />
      </template>
    </template>

    <ConfirmDialog
      v-model:is-open="showSubmitConfirm"
      :title="t('exam.confirmSubmitTitle')"
      :message="submitMessage"
      :confirm-text="t('exam.submit')"
      variant="danger"
      @confirm="confirmSubmit"
    />
  </div>
</template>

<style scoped>
.exam-booth {
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- full-bleed console padding */
  padding: 16px var(--space-9) var(--space-7);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  overflow: hidden;
}

.exam-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  margin: auto 0;
}
.exam-status--error {
  color: var(--status-danger);
}
.exam-status-actions {
  display: flex;
  justify-content: center;
  gap: var(--space-5);
  flex-wrap: wrap;
}

.briefing {
  max-width: 640px;
  margin: 0 auto;
  width: 100%;
  overflow-y: auto;
  min-height: 0;
  flex: 1;
}
.briefing-back {
  margin-bottom: var(--space-7);
}
.briefing-panel {
  padding: var(--space-10);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.briefing-eyebrow {
  margin: 0;
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-label-accent);
}
.briefing-title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--text-primary);
}
.briefing-desc {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  line-height: 1.5;
}
.briefing-ready {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-primary);
  line-height: 1.5;
}
.briefing-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-5);
}
.briefing-stat {
  background: var(--surface-page);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  padding: var(--space-5) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.briefing-stat-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
}
.briefing-stat-value {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-accent);
}
.briefing-keys {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.briefing-keys-title {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
}
.briefing-keys-hint {
  font-size: var(--font-size-md);
  color: var(--text-primary);
}
.briefing-start {
  align-self: flex-end;
}
</style>
