<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getToolList } from '../api/tool'
import { characterApi } from '../api/character'
import BaseInput from '../components/base/BaseInput.vue'
import BasePagination from '../components/base/BasePagination.vue'
import AppLayout from '../layouts/AppLayout.vue'
import { formatTokens, formatScore } from '../utils/format'

const { t } = useI18n()

function hashCode(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

const keyword = ref('')
const sortType = ref('hot')
const categoryId = ref(null)
const pageNum = ref(1)
const pageSize = ref(12)


const categoryTabs = [
  { key: 'premium', label: 'discovery.premium' },
  { key: 'recommend', label: 'discovery.recommend_rank' },
  { key: 'category', label: 'discovery.category_section' },
  { key: 'chat', label: 'discovery.chat_section' },
  { key: 'recent', label: 'discovery.recent_publish' },
]
const activeCategoryTab = ref('recommend')

const rankingTabs = [
  { key: 'daily', label: 'discovery.daily_rank' },
  { key: 'weekly', label: 'discovery.weekly_rank' },
  { key: 'monthly', label: 'discovery.monthly_rank' },
  { key: 'total', label: 'discovery.total_rank' },
  { key: 'author', label: 'discovery.author_rank' },
  { key: 'custom', label: 'discovery.custom_rank' },
]
const activeRankingTab = ref('daily')

const channelTabs = [
  { key: 'works', label: 'discovery.content_works' },
  { key: 'cards', label: 'discovery.content_character_cards' }
]
const activeChannelTab = ref('works')

const announceText = ref('2026 春 · 新故事已上线')

const categories = [
  { id: 1, name: 'categories.love', color: 'crimson' },
  { id: 2, name: 'categories.character', color: 'candy' },
  { id: 3, name: 'categories.plot', color: 'misty' },
  { id: 4, name: 'categories.fantasy', color: 'green' },
  { id: 5, name: 'categories.daily', color: 'silver' },
]

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 12 })
const loading = ref(false)

const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      keyword: keyword.value,
      sortType: sortType.value,
      pageNum: pageNum.value,
      pageSize: pageSize.value,
    }
    if (categoryId.value) params.categoryId = categoryId.value

    if (activeChannelTab.value === 'cards') {
      // Character cards channel
      const sortMap = { hot: 'hot', new: 'new', old: 'new' }
      const charParams = {
        keyword: params.keyword,
        sortType: sortMap[params.sortType] || 'hot',
        pageNum: params.pageNum,
        pageSize: params.pageSize,
      }
      if (params.categoryId) charParams.categoryId = params.categoryId
      const response = await characterApi.getList(charParams)
      // Map character fields to tool-compatible format
      const mappedList = response.data.list.map(item => {
        // Parse comma-separated text tags into [{id, name}] format
        const tagList = item.tags
          ? item.tags.split(',').filter(Boolean).map((name, i) => ({
              id: Math.abs(hashCode(name)) % 900 + 100 + i,
              name: name.trim()
            }))
          : []
        const tokens = Number(item.view_count || 0)
        const likes = Number(item.like_count || 0)
        let honorTier = null
        if (tokens >= 1000000 || likes >= 50000) honorTier = 'gold'
        else if (tokens >= 100000 || likes >= 10000) honorTier = 'silver'
        else if (tokens >= 10000) honorTier = 'bronze'
        return {
          id: item.id,
          name: item.name,
          icon: item.avatar || '',
          desc: item.description || '',
          useCount: tokens,
          likeCount: likes,
          collectCount: item.collect_count || 0,
          isFree: true,
          isVip: false,
          createTime: item.create_time,
          categoryId: item.category_id,
          tags: tagList,
          rating: item.rating || 0,
          honorTier,
          _type: 'character',
        }
      })
      listData.value.list = mappedList
      listData.value.total = response.data.total
      listData.value.pageNum = response.data.pageNum
      listData.value.pageSize = response.data.pageSize
    } else {
      // Tools/works channel
      const response = await getToolList(params)
      listData.value.list = response.data.list.map(item => ({ ...item, _type: 'tool' }))
      listData.value.total = response.data.total
      listData.value.pageNum = response.data.pageNum
      listData.value.pageSize = response.data.pageSize
    }
  } finally {
    loading.value = false
  }
}

const changeSort = (val) => {
  sortType.value = val
  pageNum.value = 1
  fetchList()
}

const handleSearch = () => {
  pageNum.value = 1
  fetchList()
}

const handlePageChange = (page) => {
  pageNum.value = page
  fetchList()
}


const getCategoryColor = (catId) => {
  const cat = categories.find(c => c.id === catId)
  return cat ? cat.color : 'misty'
}

const getTabLabel = (labelKey) => {
  return t(labelKey)
}

watch(pageNum, () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
})

watch(activeChannelTab, () => {
  pageNum.value = 1
  fetchList()
})

onMounted(fetchList)
</script>

<template>
  <AppLayout>
    <section class="explore-page animate-fade-in">
      <div class="announce-line">{{ announceText }}</div>

      <div class="top-nav">
        <span
          v-for="tab in categoryTabs"
          :key="tab.key"
          :class="['top-nav-item', { active: activeCategoryTab === tab.key }]"
          @click="activeCategoryTab = tab.key"
        >{{ getTabLabel(tab.label) }}</span>
        <span class="top-nav-divider"></span>
        <span
          v-for="tab in rankingTabs"
          :key="tab.key"
          :class="['top-nav-item top-nav-item--rank', { active: activeRankingTab === tab.key }]"
          @click="activeRankingTab = tab.key"
        >{{ getTabLabel(tab.label) }}</span>
      </div>

      <div class="toolbar-row">
        <BaseInput v-model="keyword" :placeholder="t('discovery.search_placeholder')" @keyup.enter="handleSearch" />
        <button class="action-btn" @click="handleSearch">{{ t('common.confirm') }}</button>
        <button class="action-btn ghost" type="button">{{ t('discovery.advanced_search') }}</button>
        <button class="action-btn ghost" type="button">{{ t('discovery.random') }}</button>
      </div>

      <div class="channel-tabs">
        <span
          v-for="tab in channelTabs"
          :key="tab.key"
          :class="{ active: activeChannelTab === tab.key }"
          @click="activeChannelTab = tab.key"
        >{{ t(tab.label) }}</span>
        <span class="divider" />
        <span :class="{ active: sortType === 'hot' }" @click="changeSort('hot')">{{ t('discovery.filter_hot') }}</span>
        <span :class="{ active: sortType === 'new' }" @click="changeSort('new')">{{ t('discovery.filter_new') }}</span>
        <span class="divider" />
      </div>

      <div v-if="loading" class="skeleton-grid">
        <div v-for="n in 8" :key="n" class="skeleton-card"></div>
      </div>

      <div v-else class="tool-grid">
        <router-link
          v-for="item in listData.list"
          :key="item.id"
          :to="item._type === 'character' ? `/character/${item.id}` : `/chat/${item.id}`"
          class="tool-card"
          :class="[
            `card--${getCategoryColor(item.categoryId)}`,
            item._type === 'character' ? 'card--character' : 'card--tool'
          ]"
        >
          <div class="card-accent" :class="`accent--${getCategoryColor(item.categoryId)}`"></div>
          <div :class="item._type === 'character' ? 'cover-wrap cover-wrap--char' : 'cover-wrap'">
            <div :class="item._type === 'character' ? 'tool-cover tool-cover--char' : 'tool-cover'">
              <img v-if="item.icon" :src="item.icon" :alt="item.name" class="cover-img" />
              <span v-else class="cover-text">{{ item.name.slice(0, 2) }}</span>
            </div>
            <span class="hot-badge">{{ formatTokens(item.useCount) }}</span>
            <span v-if="item.honorTier" :class="['honor-badge', `honor--${item.honorTier}`]">
              {{ { gold: '金', silver: '银', bronze: '铜' }[item.honorTier] }}
            </span>
            <div class="rating-overlay">
              <span class="rating-star">★</span>
              <span class="rating-score">{{ formatScore(item) }}</span>
            </div>
          </div>
          <div class="card-body">
            <h3 class="card-title">{{ item.name }}</h3>
            <p class="card-desc">{{ item.desc }}</p>
            <div class="card-meta">
              <span>{{ t('discovery.platform_created') }}</span>
              <span :class="item.isFree ? 'tag-free' : 'tag-vip'">
                {{ item.isFree ? t('discovery.free') : t('discovery.vip') }}
              </span>
            </div>
            <div v-if="item._type === 'character'" class="card-footer card-footer-char">
              <span class="char-stat">♥ {{ formatHot(item.likeCount) }}</span>
              <span class="char-stat">☆ {{ formatHot(item.collectCount) }}</span>
            </div>
            <div v-else class="card-footer">
              <div class="score">
                <span class="score-star">★</span>
                <span class="score-value">{{ formatScore(item) }}</span>
              </div>
              <span class="update-badge">{{ t('discovery.updated') }}</span>
            </div>
          </div>
        </router-link>
      </div>

      <div v-if="!loading && listData.list.length === 0" class="empty-state">
        <div class="empty-icon">◇</div>
        <p>{{ t('discovery.empty_content') }}</p>
        <p class="empty-hint">{{ t('discovery.empty_hint') }}</p>
      </div>

      <BasePagination
        v-if="listData.total > 0"
        :page-num="listData.pageNum"
        :page-size="listData.pageSize"
        :total="listData.total"
        @update:page-num="handlePageChange"
      />
    </section>
  </AppLayout>
</template>

<style scoped>
.explore-page {
  background: transparent;
}

/* --- Announce --- */
.announce-line {
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  margin-bottom: var(--space-sm);
  letter-spacing: 0.02em;
}

/* --- Top Nav --- */
.top-nav {
  display: flex;
  gap: 2px;
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.top-nav-item {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.top-nav-item:hover {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.03);
}

.top-nav-item.active {
  color: var(--text-primary);
  background: var(--bg-card);
  font-weight: 600;
  border-bottom: 2px solid var(--color-misty-blue-soft);
}

.top-nav-item--rank {
  font-size: var(--text-xs);
  padding: 6px 12px;
}

.top-nav-divider {
  width: 1px;
  height: 16px;
  background: var(--border-primary);
  margin: 0 2px;
  align-self: center;
}

/* --- Toolbar --- */
.toolbar-row {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  align-items: center;
}

.toolbar-row :deep(.base-input-wrap) {
  flex: 1;
}

.action-btn {
  padding: 8px 18px;
  border-radius: var(--radius-sm);
  background: var(--color-misty-blue-deep);
  color: #fff;
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.action-btn:hover {
  background: var(--color-misty-blue);
}

.action-btn.ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-input);
}

.action-btn.ghost:hover {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--text-tertiary);
}

/* --- Channel Tabs --- */
.channel-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.channel-tabs span {
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.channel-tabs span:hover {
  color: var(--text-secondary);
}

.channel-tabs span.active {
  background: var(--bg-card);
  color: var(--text-primary);
  font-weight: 600;
  border: 1px solid var(--border-card);
}

.divider {
  width: 1px;
  height: 12px;
  background: var(--border-primary);
  margin: 0 4px;
  cursor: default !important;
  padding: 0 !important;
}

/* --- Grid --- */
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
  text-decoration: none;
  display: flex;
  flex-direction: column;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-primary);
}

.card--crimson:hover {
  box-shadow: var(--shadow-glow-crimson);
  border-color: rgba(200, 85, 84, 0.3);
}

.card--candy:hover {
  box-shadow: var(--shadow-glow-pink);
  border-color: rgba(238, 162, 180, 0.3);
}

.card--misty:hover {
  box-shadow: var(--shadow-glow-misty);
  border-color: rgba(123, 156, 191, 0.3);
}

/* --- Character Card Specific --- */
.card--character {
  background: linear-gradient(180deg, rgba(238, 162, 180, 0.04) 0%, var(--bg-card) 40%);
  border-color: rgba(238, 162, 180, 0.12);
}

.card--character:hover {
  border-color: rgba(238, 162, 180, 0.3);
  box-shadow: var(--shadow-glow-pink);
}

.cover-wrap--char {
  aspect-ratio: 1/1;
}

.tool-cover--char {
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  background: linear-gradient(135deg, rgba(238, 162, 180, 0.1), rgba(200, 85, 84, 0.06));
}

/* --- Cover --- */
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
  background: rgba(0, 0, 0, 0.6);
  color: var(--color-candy-pink-soft);
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.like-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--color-crimson-soft);
  font-size: 16px;
  opacity: 0.8;
}

/* --- Card Body --- */
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

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: auto;
}

.tag-free {
  color: var(--color-dark-green-soft);
}

.tag-vip {
  color: var(--color-candy-pink);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-card);
}

.score {
  display: flex;
  align-items: center;
  gap: 4px;
}

.score-star {
  color: var(--color-candy-pink);
  font-size: var(--text-xs);
}

.score-value {
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: 600;
}

.update-badge {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.card-footer-char {
  display: flex;
  justify-content: space-around;
}

.char-stat {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

/* --- Empty --- */
.empty-state {
  text-align: center;
  padding: var(--space-3xl) var(--space-xl);
}

.empty-icon {
  font-size: 48px;
  color: var(--text-tertiary);
  opacity: 0.3;
  margin-bottom: var(--space-md);
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* --- Card Accent Strip --- */
.card-accent {
  height: 3px;
  width: 100%;
}
.accent--crimson { background: var(--color-crimson); }
.accent--candy { background: var(--color-candy-pink); }
.accent--misty { background: var(--color-misty-blue); }
.accent--green { background: var(--color-dark-green); }
.accent--silver { background: var(--color-silver-gray); }

/* --- Honor Badge --- */
.honor-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  border: 1px solid;
  z-index: 1;
}
.honor--gold {
  background: rgba(255, 193, 7, 0.15);
  color: #ffc107;
  border-color: rgba(255, 193, 7, 0.4);
}
.honor--silver {
  background: rgba(192, 192, 192, 0.12);
  color: #c0c0c0;
  border-color: rgba(192, 192, 192, 0.3);
}
.honor--bronze {
  background: rgba(205, 127, 50, 0.12);
  color: #cd7f32;
  border-color: rgba(205, 127, 50, 0.3);
}

/* --- Rating Overlay --- */
.rating-overlay {
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
.rating-star {
  color: var(--color-candy-pink);
  font-size: var(--text-xs);
}
.rating-score {
  color: var(--text-primary);
  font-size: var(--text-xs);
  font-weight: 700;
}

/* --- Enhanced Hot Badge --- */
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
  letter-spacing: 0.02em;
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .top-nav {
    gap: 0;
  }

  .top-nav-item {
    padding: 6px 10px;
    font-size: var(--text-xs);
  }

  .toolbar-row {
    flex-wrap: wrap;
  }

  .tool-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: var(--space-sm);
  }
}
</style>
