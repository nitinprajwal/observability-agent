import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
  },
  // ── Polling hook exception ────────────────────────────────────────────────
  // The "doFetch(); setInterval(doFetch)" pattern in useEffect is the standard
  // way to implement live-polling data hooks. The react-hooks/set-state-in-effect
  // rule flags this pattern as a false positive — doFetch is a stable useCallback
  // reference that sets state asynchronously (after awaiting fetch), which React
  // handles correctly. Disable the rule only for hook files.
  {
    files: ['src/hooks/**/*.{ts,tsx}'],
    rules: {
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
])
