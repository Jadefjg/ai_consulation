import vueParser from 'vue-eslint-parser'

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  {
    files: ['**/*.{js,ts}'],
    languageOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  },
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
    },
  },
]
