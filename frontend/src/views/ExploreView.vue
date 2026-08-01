<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { chatApi } from '../api/chat'
import { characterApi } from '../api/character'
import { discoveryApi } from '../api/discovery'
import BaseInput from '../components/base/BaseInput.vue'
import BasePagination from '../components/base/BasePagination.vue'
import BaseTooltip from '../components/base/BaseTooltip.vue'
import AppLayout from '../layouts/AppLayout.vue'
import { formatTokens, formatHot } from '../utils/format'

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

// ---- Category tabs ------------------------------------------------
const categoryTabs = [
  { key: 'recommend', label: 'discovery.recommend_rank' },
  { key: 'category', label: 'discovery.category_section' },
  { key: 'recent', label: 'discovery.recent_publish' },
]
const activeCategoryTab = ref('recommend')

// ---- Rankings -----------------------------------------------------
const rankingTabs = [
  { key: 'daily', label: 'discovery.daily_rank' },
  { key: 'weekly', label: 'discovery.weekly_rank' },
  { key: 'monthly', label: 'discovery.monthly_rank' },
  { key: 'total', label: 'discovery.total_rank' },
]
const activeRankingTab = ref('total')
const rankType = ref('total')

// ---- Channels -----------------------------------------------------
const channelTabs = [
  { key: 'works', label: 'discovery.content_works' },
  { key: 'cards', label: 'discovery.content_character_cards' }
]
const activeChannelTab = ref('works')

// ---- Dynamic categories from API -----------------------------------
const categories = ref([])
const categoryLoading = ref(false)

const loadCategories = async () => {
  categoryLoading.value = true
  try {
    const res = await discoveryApi.getCategories()
    categories.value = (res.data || []).map(cat => ({
      id: cat.id,
      name: cat.name,
      color: cat.color,
      icon: cat.icon,
      count: cat.count || 0,
    }))
  } catch { /* ignore */ }
  finally { categoryLoading.value = false }
}

const selectCategory = (cat) => {
  categoryId.value = cat.id
  pageNum.value = 1
  fetchList()
}

const clearCategory = () => {
  categoryId.value = null
  pageNum.value = 1
  fetchList()
}

// ---- Data list ----------------------------------------------------
const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 12 })
const loading = ref(false)

const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      keyword: keyword.value,
      sortType: sortType.value,
      rankType: rankType.value,
      pageNum: pageNum.value,
      pageSize: pageSize.value,
    }
    if (categoryId.value) params.categoryId = categoryId.value

    if (activeChannelTab.value === 'cards') {
      const sortMap = { hot: 'hot', new: 'new', old: 'new' }
      const charParams = {
        keyword: params.keyword,
        sortType: sortMap[params.sortType] || 'hot',
        rankType: params.rankType,
        pageNum: params.pageNum,
        pageSize: params.pageSize,
      }
      if (params.categoryId) charParams.category = params.categoryId
      const response = await characterApi.getList(charParams)
      const mappedList = response.data.list.map(item => {
        const tags = Array.isArray(item.tags) ? item.tags : []
        const tagList = tags.map((name, i) => ({
          id: Math.abs(hashCode(String(name))) % 900 + 100 + i,
          name: String(name).trim()
        }))
        const views = Number(item.viewCount || 0)
        const likes = Number(item.likeCount || 0)
        let honorTier = null
        if (views >= 1000000 || likes >= 50000) honorTier = 'gold'
        else if (views >= 100000 || likes >= 10000) honorTier = 'silver'
        else if (views >= 10000) honorTier = 'bronze'
        return {
          id: item.id,
          name: item.name,
          icon: item.avatar || '',
          desc: item.desc || '',
          useCount: Number(item.useCount || 0),
          likeCount: likes,
          collectCount: Number(item.collectCount || 0),
          favoritesCount: item.favoritesCount || item.collectCount || 0,
          isFree: true,
          isVip: false,
          createTime: item.createTime,
          categoryId: item.category,
          tags: tagList,
          honorTier,
          _type: 'character',
        }
      })
      listData.value.list = mappedList
      listData.value.total = response.data.total
      listData.value.pageNum = response.data.pageNum
      listData.value.pageSize = response.data.pageSize
    } else {
      const response = await chatApi.getWorks(params)
      listData.value.list = response.data.list.map(item => ({ ...item, _type: 'work' }))
      listData.value.total = response.data.total
      listData.value.pageNum = response.data.pageNum
      listData.value.pageSize = response.data.pageSize
    }
  } finally {
    loading.value = false
  }
}

// ---- Recommend tab -------------------------------------------------
const fetchRecommend = async () => {
  loading.value = true
  try {
    const params = {
      type: activeChannelTab.value === 'cards' ? 'character' : 'work',
      pageNum: pageNum.value,
      pageSize: pageSize.value,
    }
    if (categoryId.value) params.categoryId = categoryId.value

    const res = await discoveryApi.getRecommend(params)
    const mappedList = (res.data.list || []).map(item => {
      if (item._type === 'character') {
        const tags = Array.isArray(item.tags) ? item.tags : []
        const tagList = tags.map((name, i) => ({
          id: Math.abs(hashCode(String(name))) % 900 + 100 + i,
          name: String(name).trim()
        }))
        const views = Number(item.viewCount || 0)
        const likes = Number(item.likeCount || 0)
        let honorTier = null
        if (views >= 1000000 || likes >= 50000) honorTier = 'gold'
        else if (views >= 100000 || likes >= 10000) honorTier = 'silver'
        else if (views >= 10000) honorTier = 'bronze'
        return {
          id: item.id,
          name: item.name,
          icon: item.icon || '',
          desc: item.desc || '',
          useCount: Number(item.useCount || 0),
          likeCount: likes,
          collectCount: Number(item.collectCount || 0),
          favoritesCount: item.collectCount || 0,
          isFree: true,
          isVip: false,
          createTime: item.createTime,
          categoryId: item.categoryId,
          tags: tagList,
          honorTier,
          _type: 'character',
        }
      }
      return { ...item, _type: 'work' }
    })
    listData.value.list = mappedList
    listData.value.total = res.data.total
    listData.value.pageNum = res.data.pageNum
    listData.value.pageSize = res.data.pageSize
  } finally {
    loading.value = false
  }
}

// ---- Actions --------------------------------------------------------
const changeSort = (val) => {
  sortType.value = val
  pageNum.value = 1
  activeCategoryTab.value = null
  fetchList()
}

const handleSearch = () => {
  if (activeCategoryTab.value === 'recommend' || activeCategoryTab.value === 'category') {
    activeCategoryTab.value = null
  }
  pageNum.value = 1
  fetchList()
}

const handlePageChange = (page) => {
  pageNum.value = page
  if (activeCategoryTab.value === 'recommend') {
    fetchRecommend()
  } else {
    fetchList()
  }
}

const onCategoryTabClick = (tab) => {
  activeCategoryTab.value = tab.key
  pageNum.value = 1
  categoryId.value = null

  if (tab.key === 'recommend') {
    fetchRecommend()
  } else if (tab.key === 'category') {
    if (categories.value.length === 0) loadCategories()
  } else if (tab.key === 'recent') {
    sortType.value = 'new'
    fetchList()
  }
}

const onRankingTabClick = (tab) => {
  activeRankingTab.value = tab.key
  rankType.value = tab.key
  activeCategoryTab.value = null
  pageNum.value = 1
  fetchList()
}

const getCategoryColor = (catId) => {
  const cat = categories.value.find(c => c.id === catId)
  return cat ? cat.color : 'misty'
}

const getCategoryName = (catId) => {
  const cat = categories.value.find(c => c.id === catId)
  return cat ? cat.name : ''
}

const getTabLabel = (labelKey) => {
  return t(labelKey)
}

// 荣誉徽章 tooltip 文案
const honorTooltip = (tier) => {
  return { gold: '金牌作品 — 百万级热度', silver: '银牌作品 — 十万级热度', bronze: '铜牌作品 — 万级热度' }[tier] || ''
}

// ---- Watchers -------------------------------------------------------
watch(pageNum, () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
})

watch(activeChannelTab, () => {
  pageNum.value = 1
  if (activeCategoryTab.value === 'recommend') {
    fetchRecommend()
  } else {
    fetchList()
  }
})

onMounted(() => {
  fetchRecommend()
  loadCategories()
})
</script>

<template>
  <AppLayout>
    <section class="explore-page animate-fade-in">
      <div class="top-nav">
        <span
          v-for="tab in categoryTabs"
          :key="tab.key"
          :class="['top-nav-item', { active: activeCategoryTab === tab.key }]"
          @click="onCategoryTabClick(tab)"
        >{{ getTabLabel(tab.label) }}</span>
        <span class="top-nav-divider"></span>
        <span
          v-for="tab in rankingTabs"
          :key="tab.key"
          :class="['top-nav-item top-nav-item--rank', { active: activeRankingTab === tab.key }]"
          @click="onRankingTabClick(tab)"
        >{{ getTabLabel(tab.label) }}</span>
      </div>

      <div class="toolbar-row">
        <BaseInput v-model="keyword" :placeholder="t('discovery.search_placeholder')" @enter="handleSearch" />
        <button class="action-btn" @click="handleSearch">{{ t('common.confirm') }}</button>
        <button class="action-btn ghost" type="button">{{ t('discovery.random') }}</button>
      </div>

      <!-- Category grid -->
      <div v-if="activeCategoryTab === 'category' && !categoryId" class="category-section">
        <div v-if="categoryLoading" class="skeleton-grid">
          <div v-for="n in 5" :key="n" class="skeleton-card"></div>
        </div>
        <div v-else class="category-grid">
          <button
            v-for="cat in categories"
            :key="cat.id"
            :class="['category-card', `category-card--${cat.color}`]"
            @click="selectCategory(cat)"
          >
            <span class="category-icon">{{ cat.icon || '◇' }}</span>
            <span class="category-name">{{ cat.name }}</span>
            <span class="category-count">{{ cat.count }} 作品</span>
          </button>
        </div>
      </div>

      <!-- Category breadcrumb -->
      <div v-if="activeCategoryTab === 'category' && categoryId" class="category-breadcrumb">
        <span class="breadcrumb-link" @click="clearCategory">{{ t('discovery.category_section') }}</span>
        <span class="breadcrumb-sep">&rsaquo;</span>
        <span class="breadcrumb-current">{{ getCategoryName(categoryId) }}</span>
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
          :to="item._type === 'character' ? `/chat/character/${item.id}` : `/chat/${item.id}`"
          class="tool-card"
          :class="[
            `card--${getCategoryColor(item.categoryId)}`,
            item._type === 'character' ? 'card--character' : 'card--tool'
          ]"
        >
          <!-- 顶部炫彩条 -->
          <div class="card-accent" :class="`accent--${getCategoryColor(item.categoryId)}`"></div>

          <!-- 封面 -->
          <div :class="item._type === 'character' ? 'cover-wrap cover-wrap--char' : 'cover-wrap'">
            <div :class="item._type === 'character' ? 'tool-cover tool-cover--char' : 'tool-cover'">
              <img v-if="item.icon" :src="item.icon" :alt="item.name" class="cover-img" />
              <span v-else class="cover-text">{{ item.name.slice(0, 2) }}</span>
            </div>
            <!-- 封面渐变遮罩 -->
            <div class="cover-gradient"></div>

            <!-- 热度角标 -->
            <span class="hot-badge">🔥 {{ formatTokens(item.useCount) }}</span>

            <!-- 荣誉角标 -->
            <BaseTooltip v-if="item.honorTier" :text="honorTooltip(item.honorTier)">
              <span :class="['honor-badge', `honor--${item.honorTier}`]">
                {{ { gold: '👑 金', silver: '🥈 银', bronze: '🥉 铜' }[item.honorTier] }}
              </span>
            </BaseTooltip>

            <!-- 收藏数 -->
            <div class="rating-overlay">
              <span class="favorite-heart">♥</span>
              <span class="favorite-count">{{ formatHot(item.favoritesCount) }}</span>
            </div>
          </div>

          <!-- 卡片内容 -->
          <div class="card-body">
            <BaseTooltip :text="item.name">
              <h3 class="card-title">{{ item.name }}</h3>
            </BaseTooltip>
            <BaseTooltip :text="item.desc">
              <p class="card-desc">{{ item.desc }}</p>
            </BaseTooltip>

            <!-- 标签 -->
            <div v-if="item.tags && item.tags.length > 0" class="card-tags">
              <span v-for="tag in item.tags.slice(0, 3)" :key="tag.id" class="card-tag">{{ tag.name }}</span>
            </div>

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

/* --- Card --- */
.tool-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  overflow: hidden;
  transition: all var(--transition-base);
  text-decoration: none;
  display: flex;
  flex-direction: column;
  position: relative;
}

.tool-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-xl);
  border-color: var(--border-primary);
}

.card--crimson:hover {
  box-shadow: var(--shadow-glow-crimson), var(--shadow-lg);
  border-color: rgba(200, 85, 84, 0.4);
}

.card--candy:hover {
  box-shadow: var(--shadow-glow-pink), var(--shadow-lg);
  border-color: rgba(238, 162, 180, 0.4);
}

.card--misty:hover {
  box-shadow: var(--shadow-glow-misty), var(--shadow-lg);
  border-color: rgba(123, 156, 191, 0.4);
}

.card--green:hover {
  box-shadow: 0 0 20px rgba(61, 107, 86, 0.2), var(--shadow-lg);
  border-color: rgba(61, 107, 86, 0.4);
}

/* --- Character Card Specific --- */
.card--character {
  background: linear-gradient(180deg, rgba(238, 162, 180, 0.06) 0%, var(--bg-card) 35%);
  border-color: rgba(238, 162, 180, 0.15);
}

.card--character:hover {
  border-color: rgba(238, 162, 180, 0.4);
  box-shadow: var(--shadow-glow-pink), var(--shadow-lg);
}

.cover-wrap--char {
  aspect-ratio: 1/1;
}

.tool-cover--char {
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  background: linear-gradient(135deg, rgba(238, 162, 180, 0.12), rgba(200, 85, 84, 0.08));
}

/* --- Cover --- */
.cover-wrap {
  position: relative;
  aspect-ratio: 4/3;
  overflow: hidden;
}

.cover-gradient {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.5));
  pointer-events: none;
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
  transition: transform 0.4s ease;
}

.tool-card:hover .cover-img {
  transform: scale(1.05);
}

.cover-text {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-tertiary);
  opacity: 0.3;
}

/* --- Hot Badge --- */
.hot-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: linear-gradient(135deg, rgba(200, 85, 84, 0.88), rgba(238, 162, 180, 0.72));
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.02em;
  z-index: 1;
  box-shadow: 0 2px 6px rgba(200, 85, 84, 0.25);
}

/* --- Honor Badge --- */
.honor-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid;
  z-index: 1;
  letter-spacing: 0.05em;
  backdrop-filter: blur(4px);
  cursor: default;
}

.honor--gold {
  background: rgba(255, 193, 7, 0.18);
  color: #ffd54f;
  border-color: rgba(255, 193, 7, 0.5);
  box-shadow: 0 0 10px rgba(255, 193, 7, 0.12);
}

.honor--silver {
  background: rgba(192, 192, 192, 0.14);
  color: #e0e0e0;
  border-color: rgba(192, 192, 192, 0.35);
}

.honor--bronze {
  background: rgba(205, 127, 50, 0.14);
  color: #dea060;
  border-color: rgba(205, 127, 50, 0.35);
}

/* --- Rating Overlay --- */
.rating-overlay {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 1;
}

.favorite-heart {
  color: var(--color-crimson-soft);
  font-size: 11px;
}

.favorite-count {
  color: var(--text-primary);
  font-size: 11px;
  font-weight: 700;
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
  letter-spacing: 0.01em;
}

.card-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

/* --- Tags --- */
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.card-tag {
  display: inline-block;
  padding: 1px 7px;
  font-size: 10px;
  background: rgba(123, 156, 191, 0.1);
  color: var(--color-misty-blue-soft);
  border-radius: var(--radius-sm);
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
  font-weight: 500;
}

/* --- Card Accent Strip --- */
.card-accent {
  height: 3px;
  width: 100%;
}

.accent--crimson {
  background: linear-gradient(90deg, var(--color-crimson-deep), var(--color-crimson), var(--color-candy-pink));
}

.accent--candy {
  background: linear-gradient(90deg, var(--color-candy-pink-deep), var(--color-candy-pink));
}

.accent--misty {
  background: linear-gradient(90deg, var(--color-misty-blue-deep), var(--color-misty-blue), var(--color-misty-blue-soft));
}

.accent--green {
  background: linear-gradient(90deg, var(--color-dark-green-deep), var(--color-dark-green));
}

.accent--silver {
  background: linear-gradient(90deg, var(--color-silver-gray-deep), var(--color-silver-gray));
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

/* --- Category Grid --- */
.category-section {
  margin-bottom: var(--space-md);
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--space-sm);
}

.category-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: var(--space-lg) var(--space-md);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.category-card:hover {
  transform: translateY(-3px);
}

.category-card--crimson:hover { border-color: var(--color-crimson); box-shadow: var(--shadow-glow-crimson); }
.category-card--candy:hover { border-color: var(--color-candy-pink); box-shadow: var(--shadow-glow-pink); }
.category-card--misty:hover { border-color: var(--color-misty-blue); box-shadow: var(--shadow-glow-misty); }
.category-card--green:hover { border-color: var(--color-dark-green); }
.category-card--silver:hover { border-color: var(--color-silver-gray); }

.category-icon {
  font-size: 22px;
  opacity: 0.7;
}

.category-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
}

.category-count {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.category-breadcrumb {
  margin-bottom: var(--space-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.breadcrumb-link {
  color: var(--color-misty-blue-soft);
  cursor: pointer;
}

.breadcrumb-link:hover {
  text-decoration: underline;
}

.breadcrumb-sep {
  color: var(--text-tertiary);
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 600;
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
