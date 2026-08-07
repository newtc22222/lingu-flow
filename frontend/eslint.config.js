import vuePlugin from 'eslint-plugin-vue';
import vueParser from 'vue-eslint-parser';
import tsParser from '@typescript-eslint/parser';
import localRules from './eslint-local-rules/no-raw-tailwind-palette.js';

export default [
  {
    files: ['src/**/*.vue'],
    plugins: {
      vue: vuePlugin,
      local: { rules: localRules },
    },
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        parser: tsParser,
      },
    },
    rules: {
      'local/no-raw-tailwind-palette': 'error',
    },
  },
];
