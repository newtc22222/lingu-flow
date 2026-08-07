import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { inject } from '@vercel/analytics';

import '@fontsource/press-start-2p';
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-sans/700.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import '@fontsource/ibm-plex-mono/700.css';
import './style.css';

import App from './App.vue';
import { i18n } from './i18n';
import { router } from './router';

inject();

// Pinia must be installed before the router: the `beforeEach` auth guard
// resolves `useAuthStore()`, which needs an active Pinia instance.
createApp(App).use(createPinia()).use(i18n).use(router).mount('#app');
