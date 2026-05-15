<script setup>
import { onMounted, ref } from 'vue'
import { getToolList } from '../api/tool'
import { collectRecord, getRecordList, getUserInfo, updateUserInfo } from '../api/user'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import BasePagination from '../components/base/BasePagination.vue'
import AppLayout from '../layouts/AppLayout.vue'

const auth = useAuthStore()

const activeMenu = ref('history')
const user = ref({ nickname: '', avatar: '', vipLevel: 0, vipExpireTime: null, phone: '', email: '' })
const records = ref({ list: [], total: 0, pageNum: 1, pageSize: 10 })
const recentTools = ref({ list: [], total: 0 })
const editForm = ref({ nickname: '', avatar: '' })
const recordLoading = ref(false)
const saveLoading = ref(false)

const menuItems = [
  { key: 'history', label: '创作历史', icon: '📜' },
  { key: 'favorites', label: '我的收藏', icon: '♥' },
  { key: 'recent', label: '最近使用', icon: '🕐' },
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

const fetchRecords = async () => {
  recordLoading.value = true
  try {
    const res = await getRecordList({ pageNum: records.value.pageNum, pageSize: records.value.pageSize })
    records.value.list = res.data.list
    records.value.total = res.data.total
    records.value.pageNum = res.data.pageNum
    records.value.pageSize = res.data.pageSize
  } finally {
    recordLoading.value = false
  }
}

const fetchRecentTools = async () => {
  try {
    const res = await getToolList({ pageSize: 20 })
    recentTools.value = res.data
  } catch {}
}

const handleRecordPageChange = (page) => {
  records.value.pageNum = page
  fetchRecords()
}

const handleCollect = async (recordId) => {
  try {
    await collectRecord(recordId)
    fetchRecords()
  } catch {}
}

const handleSaveInfo = async () => {
  saveLoading.value = true
  try {
    await updateUserInfo({ nickname: editForm.value.nickname, avatar: editForm.value.avatar })
    user.value.nickname = editForm.value.nickname
    user.value.avatar = editForm.value.avatar
    auth.updateUserInfo({ nickname: editForm.value.nickname, avatar: editForm.value.avatar })
    window.dispatchEvent(new CustomEvent('app:error', { detail: '保存成功' }))
  } catch (err) {
    window.dispatchEvent(new CustomEvent('app:error', { detail: err.message || '保存失败' }))
  } finally {
    saveLoading.value = false
  }
}

const switchMenu = (key) => {
  activeMenu.value = key
  if (key === 'history') fetchRecords()
  if (key === 'recent') fetchRecentTools()
}

onMounted(async () => {
  await fetchUserInfo()
  fetchRecords()
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
              <span class="pstat-value">{{ records.total }}</span>
              <span class="pstat-label">作品</span>
            </div>
            <div class="pstat">
              <span class="pstat-value">{{ recentTools.total }}</span>
              <span class="pstat-label">工具</span>
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

          <template v-if="activeMenu === 'history'">
            <div v-if="recordLoading" class="skeleton-list">
              <div v-for="n in 5" :key="n" class="skeleton-item"></div>
            </div>
            <div v-else-if="records.list.length === 0" class="empty">
              <div class="empty-icon">◇</div>
              <p>暂无创作记录</p>
            </div>
            <div v-else class="record-list">
              <div v-for="item in records.list" :key="item.recordId" class="record-item">
                <div class="record-info">
                  <div class="record-header">
                    <span class="tool-name">{{ item.toolName }}</span>
                    <span :class="['status', item.status === 1 ? 'success' : 'pending']">
                      {{ item.status === 1 ? '已完成' : '生成中' }}
                    </span>
                  </div>
                  <span class="record-time">{{ item.createTime }}</span>
                </div>
                <div class="record-result" v-if="item.result">
                  {{ item.result.slice(0, 200) }}{{ item.result.length > 200 ? '…' : '' }}
                </div>
                <div class="record-actions">
                  <button class="collect-btn" @click="handleCollect(item.recordId)">
                    {{ item.isCollected ? '♥ 已收藏' : '♡ 收藏' }}
                  </button>
                </div>
              </div>
            </div>
            <BasePagination
              v-if="records.total > 0"
              :page-num="records.pageNum"
              :page-size="records.pageSize"
              :total="records.total"
              @update:page-num="handleRecordPageChange"
            />
          </template>

          <template v-if="activeMenu === 'favorites'">
            <div class="empty">
              <div class="empty-icon">♥</div>
              <p>收藏功能开发中</p>
              <p class="empty-hint">通过历史记录可以收藏喜欢的创作</p>
            </div>
          </template>

          <template v-if="activeMenu === 'recent'">
            <div v-if="recentTools.list.length === 0" class="empty">
              <div class="empty-icon">🕐</div>
              <p>暂无最近使用记录</p>
            </div>
            <div v-else class="simple-list">
              <div v-for="item in recentTools.list" :key="item.id" class="simple-item">
                <span class="simple-name">{{ item.name }}</span>
                <span class="simple-time">{{ item.lastUseTime }}</span>
              </div>
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
