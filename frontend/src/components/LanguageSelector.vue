<script setup>
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const languages = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: 'English' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
]

const changeLanguage = (lang) => {
  locale.value = lang
  localStorage.setItem('userLanguage', lang)
  // Send language preference to backend if user is logged in
  // This would require the user store and API call
}
</script>

<template>
  <div class="language-selector">
    <select 
      v-model="locale" 
      @change="changeLanguage(locale)"
      class="language-select"
    >
      <option 
        v-for="lang in languages" 
        :key="lang.code" 
        :value="lang.code"
      >
        {{ lang.name }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.language-selector {
  display: inline-block;
}

.language-select {
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-input);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.language-select:hover {
  border-color: var(--border-primary);
}

.language-select:focus {
  outline: none;
  border-color: var(--color-misty-blue-deep);
}
</style>
