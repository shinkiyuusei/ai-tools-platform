<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getUserInfo, updateUserInfo } from '../api/user'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import RechargeModal from '../components/RechargeModal.vue'
import AppLayout from '../layouts/AppLayout.vue'
import { notifySuccess, notifyError } from '../utils/notify'

const router = useRouter()
const auth = useAuthStore()

const activeMenu = ref('account')
const user = ref({ nickname: '', avatar: '', vipLevel: 0, vipExpireTime: null, phone: '', email: '' })
const editForm = ref({ nickname: '', avatar: '' })
const saveLoading = ref(false)
const showRechargeModal = ref(false)

const menuItems = [
  { key: 'recharge', label: '积分充值', icon: '💰', action: 'recharge' },
  { key: 'characters', label: '我的角色', icon: '◇', route: '/my-characters' },
  { key: 'works', label: '我的作品', icon: '◇', route: '/my-works' },
  { key: 'favorites', label: '我的收藏', icon: '♥', route: '/favorites' },
  { key: 'account', label: '账号设置', icon: '⚙' },
  { key: 'security', label: '安全中心', icon: '🔒' },
]

const fetchUserInfo = async () => {
  try {
    const res = await getUserInfo()
    user.value = res.data
    auth.updateUserInfo(res.data)
    editForm.value = { nickname: res.data.nickname || '', avatar: res.data.avatar || '' }
  } catch {}
}

const handleSaveInfo = async () => {
  saveLoading.value = true
  try {
    await updateUserInfo({ nickname: editForm.value.nickname, avatar: editForm.value.avatar })
    user.value.nickname = editForm.value.nickname
    user.value.avatar = editForm.value.avatar
    auth.updateUserInfo({ nickname: editForm.value.nickname, avatar: editForm.value.avatar })
    notifySuccess('保存成功')
  } catch (err) {
    notifyError(err.message || '保存失败')
  } finally {
    saveLoading.value = false
  }
}

const switchMenu = (key) => {
  const item = menuItems.find(m => m.key === key)
  if (item?.action === 'recharge') {
    showRechargeModal.value = true
    return
  }
  if (item?.route) {
    router.push(item.route)
    return
  }
  activeMenu.value = key
}

onMounted(async () => {
  await fetchUserInfo()
})
</script>

<template>
  <AppLayout>
    <section class="user-layout animate-fade-in">
      <aside class="user-sidebar">
        <div class="profile-card gradient-hero">
          <div class="avatar-circle">{{ user.nickname?.charAt(0) || 'U' }}</div>
          <h2>{{ user.nickname || '创作者' }}</h2>
          <span class="vip-badge">创作者</span>
          <div class="profile-stats">
            <div class="pstat">
              <span class="pstat-value">{{ user.vipLevel >= 1 ? '会员' : '免费' }}</span>
              <span class="pstat-label">状态</span>
            </div>
          </div>
        </div>
        <div class="menu-list">
          <div
            v-for="item in menuItems"
            :key="item.key"
            :class="['menu-item', { active: activeMenu === item.key }]"
            @click="switchMenu(item.key)"
          >
            <span class="menu-item-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </aside>

      <div class="user-main">
        <div class="panel">
          <div class="panel-header">
            <h1>{{ menuItems.find(m => m.key === activeMenu)?.label }}</h1>
          </div>

          <template v-if="activeMenu === 'favorites'">
            <div class="empty">
              <div class="empty-icon">♥</div>
              <p>前往收藏页面查看收藏的作品</p>
              <p class="empty-hint">
                <router-link to="/favorites">→ 我的收藏</router-link>
              </p>
            </div>
          </template>

          <template v-if="activeMenu === 'account'">
            <div class="form-card">
              <div class="form-row">
                <label>昵称</label>
                <BaseInput v-model="editForm.nickname" placeholder="请输入昵称" />
              </div>
              <div class="form-row">
                <label>头像</label>
                <BaseInput v-model="editForm.avatar" placeholder="请输入头像链接" />
              </div>
              <div class="form-row">
                <label>手机号</label>
                <span class="readonly">{{ user.phone || '未绑定' }}</span>
              </div>
              <div class="form-row">
                <label>邮箱</label>
                <span class="readonly">{{ user.email || '未绑定' }}</span>
              </div>
              <BaseButton :loading="saveLoading" @click="handleSaveInfo">保存修改</BaseButton>
            </div>
          </template>

          <template v-if="activeMenu === 'security'">
            <div class="form-card">
              <div class="form-row">
                <label>修改密码</label>
                <span class="readonly">通过忘记密码功能修改</span>
              </div>
              <router-link to="/forgot-password">
                <BaseButton variant="secondary">前往修改密码</BaseButton>
              </router-link>
            </div>
          </template>
        </div>
      </div>
    </section>

    <!-- 充值弹窗 -->
    <RechargeModal v-if="showRechargeModal" @close="showRechargeModal = false" />
  </AppLayout>
</template>

<style scoped>
.user-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: var(--space-lg);
}

/* --- Sidebar --- */
.user-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.profile-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-secondary);
  padding: var(--space-xl) var(--space-lg);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.avatar-circle {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-misty-blue));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xl);
  font-weight: 700;
  color: #fff;
  box-shadow: var(--shadow-glow-misty);
}

.profile-card h2 {
  font-size: var(--text-lg);
  margin: 0;
}

.vip-badge {
  font-size: var(--text-xs);
  color: var(--color-candy-pink);
  background: rgba(238, 162, 180, 0.1);
  padding: 2px 12px;
  border-radius: var(--radius-full);
}

.profile-stats {
  display: flex;
  gap: var(--space-xl);
  margin-top: var(--space-sm);
}

.pstat {
  text-align: center;
}

.pstat-value {
  display: block;
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.pstat-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.menu-list {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.menu-item:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.menu-item.active {
  background: rgba(123, 156, 191, 0.1);
  color: var(--color-misty-blue-soft);
  font-weight: 500;
}

/* --- Main --- */
.user-main {
  min-width: 0;
}

.panel {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
  min-height: 400px;
}

.panel-header {
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--border-card);
}

.panel-header h1 {
  font-size: var(--text-lg);
  margin: 0;
}

/* --- Empty --- */
.empty {
  text-align: center;
  padding: var(--space-3xl) var(--space-xl);
}

.empty-icon {
  font-size: 40px;
  opacity: 0.3;
  margin-bottom: var(--space-md);
}

.empty p {
  color: var(--text-secondary);
}

.empty-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* --- Record List --- */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skeleton-item {
  height: 80px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  animation: shimmer 1.5s infinite;
  background-size: 200% 100%;
  background-image: linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-card) 50%, var(--bg-elevated) 75%);
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.record-item {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-card);
  padding: var(--space-md);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}

.tool-name {
  font-weight: 600;
  font-size: var(--text-sm);
}

.status {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.status.success {
  background: rgba(61, 107, 86, 0.12);
  color: var(--color-dark-green-soft);
}

.status.pending {
  background: rgba(238, 162, 180, 0.1);
  color: var(--color-candy-pink);
}

.record-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.record-result {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin: var(--space-sm) 0;
  line-height: var(--leading-relaxed);
}

.record-actions {
  display: flex;
  gap: var(--space-sm);
}

.collect-btn {
  font-size: var(--text-xs);
  color: var(--color-candy-pink-soft);
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.collect-btn:hover {
  opacity: 0.7;
}

/* --- Simple List --- */
.simple-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.simple-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.simple-item:hover {
  background: var(--bg-tertiary);
}

.simple-name {
  font-size: var(--text-sm);
  color: var(--text-primary);
}

.simple-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* --- Form --- */
.form-card {
  max-width: 480px;
}

.form-row {
  margin-bottom: var(--space-lg);
}

.form-row label {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
  font-weight: 500;
}

.readonly {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .user-layout {
    grid-template-columns: 1fr;
  }

  .user-sidebar {
    order: -1;
  }

  .profile-card {
    padding: var(--space-lg);
  }

  .panel {
    padding: var(--space-md);
  }
}
</style>
