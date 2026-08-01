import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'
import ja from './locales/ja.json'
import ko from './locales/ko.json'

const messages = { zh, en, ja, ko }
const LOCALES = ['zh', 'en', 'ja', 'ko']

// 从 URL path 或 localStorage 读取 locale
function detectLocale() {
  const pathSeg = window.location.pathname.split('/').filter(Boolean)
  if (pathSeg.length > 0 && LOCALES.includes(pathSeg[0])) {
    return pathSeg[0]
  }
  return localStorage.getItem('userLanguage') || 'zh'
}

const i18n = createI18n({
  legacy: false,
  locale: detectLocale(),
  fallbackLocale: 'zh',
  messages,
})

export default i18n
