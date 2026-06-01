import { createRouter, createWebHistory } from 'vue-router'

import CharacterChatView from '../views/CharacterChatView.vue'
import CharacterDetailView from '../views/CharacterDetailView.vue'
import ChatView from '../views/ChatView.vue'
import ErrorView from '../views/ErrorView.vue'
import FavoritesView from '../views/FavoritesView.vue'
import ExploreView from '../views/ExploreView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import UserCenterView from '../views/UserCenterView.vue'
import CharacterCardView from '../views/CharacterCardView.vue'
import WorkCardView from '../views/WorkCardView.vue'
import CharacterManageView from '../views/admin/CharacterManageView.vue'
import TagManageView from '../views/admin/TagManageView.vue'
import UserManageView from '../views/admin/UserManageView.vue'
import WorkManageView from '../views/admin/WorkManageView.vue'

const routes = [
  { path: '/', redirect: '/explore' },
  { path: '/create', name: 'home', component: HomeView },
  { path: '/explore', name: 'explore', component: ExploreView },
  { path: '/chat/:workId', name: 'chat', component: ChatView },
  { path: '/chat/character/:id', name: 'character-chat', component: CharacterChatView },
  { path: '/character/:id', name: 'character-detail', component: CharacterDetailView },
  { path: '/usercenter', name: 'user-center', component: UserCenterView, meta: { requiresAuth: true } },
  { path: '/my-characters', name: 'my-characters', component: CharacterCardView, meta: { requiresAuth: true } },
  { path: '/my-works', name: 'my-works', component: WorkCardView, meta: { requiresAuth: true } },
  { path: '/favorites', name: 'favorites', component: FavoritesView, meta: { requiresAuth: true } },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
  { path: '/error/:code', name: 'error', component: ErrorView, props: true },
  { path: '/admin/tag', name: 'admin-tag', component: TagManageView, meta: { requiresAuth: true } },
  { path: '/admin/user', name: 'admin-user', component: UserManageView, meta: { requiresAuth: true } },
  { path: '/admin/character', name: 'admin-character', component: CharacterManageView, meta: { requiresAuth: true } },
  { path: '/admin/work', name: 'admin-work', component: WorkManageView, meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: ErrorView, props: { code: 404 } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function isAdmin() {
  const userInfo = localStorage.getItem('userInfo')
  if (!userInfo) return false
  try {
    return (JSON.parse(userInfo)?.vipLevel || 0) >= 2
  } catch {
    return false
  }
}

router.beforeEach(async (to) => {
  const userInfo = localStorage.getItem('userInfo')
  const hasUser = !!userInfo

  if (to.meta.requiresAuth && !hasUser) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.path.startsWith('/admin') && !isAdmin()) {
    return { name: 'explore' }
  }

  return true
})

export default router
