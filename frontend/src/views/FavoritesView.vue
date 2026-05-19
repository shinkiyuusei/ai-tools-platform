<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getCollectedTools } from '../api/user'
import BasePagination from '../components/base/BasePagination.vue'
import AppLayout from '../layouts/AppLayout.vue'
import { formatTokens, formatHot } from '../utils/format'

const router = useRouter()

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 12 })
const loading = ref(false)

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getCollectedTools({
      pageNum: listData.value.pageNum,
      pageSize: listData.value.pageSize,
    })
    listData.value.list = res.data.list
    listData.value.total = res.data.total
    listData.value.pageNum = res.data.pageNum
    listData.value.pageSize = res.data.pageSize
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  listData.value.pageNum = page
  fetchList()
}

const goToChat = (id) => {
  router.push(`/chat/${id}`)
}

onMounted(fetchList)
</script>

<template>
  <AppLayout>
    <div class="page">
      <div class="page-header">
        <h1>♥ 我的收藏</h1>
        <span class="total-hint">共 {{ listData.total }} 个作品</span>
      </div>

      <div v-if="loading" class="skeleton-grid">
        <div v-for="n in 8" :key="n" class="skeleton-card" />
      </div>

      <div v-else-if="listData.list.length" class="tool-grid">
        <div
          v-for="item in listData.list"
          :key="item.id"
          class="tool-card"
          @click="goToChat(item.id)"
        >
          <div class="cover-wrap">
            <div class="tool-cover">
              <img v-if="item.icon && item.icon.startsWith('http')" :src="item.icon" :alt="item.name" class="cover-img" />
              <span v-else class="cover-text">{{ item.name.slice(0, 2) }}</span>
            </div>
            <span class="hot-badge">{{ formatTokens(item.useCount) }}</span>
            <div class="fav-overlay">
              <span class="fav-heart">♥</span>
              <span class="fav-count">{{ formatHot(item.favoritesCount) }}</span>
            </div>
          </div>
          <div class="card-body">
            <h3 class="card-title">{{ item.name }}</h3>
            <p class="card-desc">{{ item.desc }}</p>
            <div class="card-footer">
              <span class="card-type">{{ item.isFree ? '免费' : 'VIP' }}</span>
              <span class="card-score" v-if="item.rating">★ {{ Number(item.rating).toFixed(1) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">♥</div>
        <p>暂无收藏</p>
        <p class="empty-hint">去发现页看看有没有喜欢的作品吧</p>
        <button class="go-explore-btn" @click="router.push('/explore')">去发现页</button>
      </div>

      <BasePagination
        v-if="listData.total > 0"
        :page-num="listData.pageNum"
        :page-size="listData.pageSize"
        :total="listData.total"
        @update:page-num="handlePageChange"
      />
    </div>
  </AppLayout>
</template>

<style scoped>
.page {
  background: transparent;
}

.page-header {
  display: flex;
  align-items: baseline;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.page-header h1 {
  font-size: var(--text-xl);
  margin: 0;
  color: var(--text-primary);
}

.total-hint {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* Grid -- 复用 Explore 样式 */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-lg);
}

.skeleton-card {
  aspect-ratio: 3/4;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  animation: shimmer 1.5s infinite;
  background-size: 200% 100%;
  background-image: linear-gradient(90deg, var(--bg-card) 25%, var(--bg-elevated) 50%, var(--bg-card) 75%);
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-lg);
}

.tool-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  overflow: hidden;
  transition: all var(--transition-base);
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-primary);
}

/* Cover */
.cover-wrap {
  position: relative;
  aspect-ratio: 4/3;
  overflow: hidden;
}

.tool-cover {
  width: 100%;
  height: 100%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-text {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-tertiary);
  opacity: 0.3;
}

.hot-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: linear-gradient(135deg, rgba(200, 85, 84, 0.85), rgba(238, 162, 180, 0.65));
  color: #fff;
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.fav-overlay {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.65);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 3px;
}

.fav-heart {
  color: var(--color-crimson-soft);
  font-size: var(--text-xs);
}

.fav-count {
  color: var(--text-primary);
  font-size: var(--text-xs);
  font-weight: 700;
}

/* Card Body */
.card-body {
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  flex: 1;
}

.card-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-card);
  margin-top: auto;
}

.card-type {
  font-size: var(--text-xs);
  color: var(--color-dark-green-soft);
}

.card-score {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

/* Empty */
.empty-state {
  text-align: center;
  padding: var(--space-3xl) var(--space-xl);
}

.empty-icon {
  font-size: 48px;
  color: var(--color-crimson-soft);
  opacity: 0.5;
  margin-bottom: var(--space-md);
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--space-lg);
}

.go-explore-btn {
  padding: 8px 24px;
  border-radius: var(--radius-sm);
  background: var(--color-misty-blue-deep);
  color: #fff;
  font-size: var(--text-sm);
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.go-explore-btn:hover {
  background: var(--color-misty-blue);
}

@media (max-width: 768px) {
  .tool-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: var(--space-sm);
  }
}
</style>
