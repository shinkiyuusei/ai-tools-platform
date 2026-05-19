import { createRouter, createWebHistory } from 'vue-router'

import CharacterDetailView from '../views/CharacterDetailView.vue'
import ChatView from '../views/ChatView.vue'
import ErrorView from '../views/ErrorView.vue'
import ExploreView from '../views/ExploreView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ToolDetailView from '../views/ToolDetailView.vue'
import UserCenterView from '../views/UserCenterView.vue'
import CharacterManageView from '../views/admin/CharacterManageView.vue'
import TagManageView from '../views/admin/TagManageView.vue'
import ToolManageView from '../views/admin/ToolManageView.vue'

const routes = [
  { path: '/', redirect: '/explore' },
  { path: '/create', name: 'home', component: HomeView },
  { path: '/explore', name: 'explore', component: ExploreView },
  { path: '/tool/:toolId', name: 'tool-detail', component: ToolDetailView, props: true },
  { path: '/chat/:workId', name: 'chat', component: ChatView },
  { path: '/character/:id', name: 'character-detail', component: CharacterDetailView },
  { path: '/usercenter', name: 'user-center', component: UserCenterView, meta: { requiresAuth: true } },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
  { path: '/error/:code', name: 'error', component: ErrorView, props: true },
  { path: '/admin/tag', name: 'admin-tag', component: TagManageView, meta: { requiresAuth: true } },
  { path: '/admin/tool', name: 'admin-tool', component: ToolManageView, meta: { requiresAuth: true } },
  { path: '/admin/character', name: 'admin-character', component: CharacterManageView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: ErrorView, props: { code: 404 } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function checkIsAdmin() {
  const token = localStorage.getItem('token')
  if (!token) return false
  try {
    const raw = localStorage.getItem('userInfo')
    const userInfo = raw ? JSON.parse(raw) : null
    return (userInfo?.vipLevel || 0) >= 2
  } catch {
    return false
  }
}

router.beforeEach((to) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.path.startsWith('/admin') && !checkIsAdmin()) {
    return { name: 'explore' }
  }

  return true
})

export default router
