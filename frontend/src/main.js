import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { loadExtensions } from './services/extensionLoader'
import './styles/index.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')

// 隐藏首屏 Loading 骨架
const loadingEl = document.getElementById('app-loading')
if (loadingEl) {
  loadingEl.classList.add('hidden')
  setTimeout(() => loadingEl.remove(), 350)
}

// Boot the extension system after the app is mounted.
loadExtensions({}).catch(e => console.error('Extension boot failed:', e))
