const eslint = require('@eslint/js')
const tseslint = require('typescript-eslint')

module.exports = tseslint.config(
  { ignores: ['dist/', 'release/', 'node_modules/', '*.config.*', 'tests_e2e/'] },
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': 'warn',
    },
  },
)
