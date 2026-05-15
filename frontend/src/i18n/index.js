import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'
import ja from './locales/ja.json'
import ko from './locales/ko.json'

const messages = {
  zh,
  en,
  ja,
  ko
}

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('userLanguage') || 'zh',
  fallbackLocale: 'zh',
  messages,
})

export default i18n
