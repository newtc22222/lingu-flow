import { createI18n } from 'vue-i18n';
import en from '@/locales/en.json';
import vi from '@/locales/vi.json';

export const SUPPORTED_LOCALES = ['vi', 'en'] as const;
export type AppLocale = (typeof SUPPORTED_LOCALES)[number];

const LOCALE_KEY = 'locale';

function resolveInitialLocale(): AppLocale {
  const stored = localStorage.getItem(LOCALE_KEY);
  if (stored && (SUPPORTED_LOCALES as readonly string[]).includes(stored)) {
    return stored as AppLocale;
  }
  // The product is Vietnamese-first — only fall back to English for a browser
  // that explicitly isn't Vietnamese.
  return navigator.language.startsWith('vi') ? 'vi' : 'en';
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale: 'vi',
  messages: { vi, en },
});

export function setLocale(locale: AppLocale) {
  i18n.global.locale.value = locale;
  localStorage.setItem(LOCALE_KEY, locale);
  document.documentElement.lang = locale;
}

document.documentElement.lang = i18n.global.locale.value;
