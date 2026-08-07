<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<template>
  <footer class="app-footer font-label">
    <div class="footer-inner">
      <div class="footer-brand font-pixel">{{ t('auth.footerBrand') }}</div>
      <div class="footer-links">
        <span class="footer-link">{{ t('auth.footerProtocol') }}</span>
        <span class="footer-link">{{ t('auth.footerDocs') }}</span>
        <span class="footer-link">{{ t('auth.footerSupport') }}</span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  width: 100%;
  border-top: var(--space-1) solid var(--surface-panel-border);
  background: var(--surface-page);
  padding: var(--space-6) var(--space-8);
  margin-top: auto;
  z-index: 10;
  box-sizing: border-box;
}

.footer-inner {
  max-width: 1024px;
  margin: 0 auto;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.footer-brand {
  color: var(--color-accent);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-normal);
}

.footer-links {
  display: flex;
  gap: var(--space-6);
}

.footer-link {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  cursor: pointer;
  transition: color 0.15s ease;
}

.footer-link:hover {
  color: var(--color-accent);
}
</style>
