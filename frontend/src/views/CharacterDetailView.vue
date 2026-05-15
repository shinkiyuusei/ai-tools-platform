<template>
  <AppLayout>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="character" class="character-detail animate-fade-in">
      <div class="cover-section">
        <img v-if="character.avatar" :src="character.avatar" :alt="character.name" class="cover-img" />
        <div v-else class="cover-placeholder">{{ character.name.slice(0, 2) }}</div>
        <div class="cover-overlay">
          <h1>{{ character.name }}</h1>
          <div class="stats-row">
            <span class="stat">♥ {{ character.like_count || 0 }}</span>
            <span class="stat">👁 {{ formatViews(character.view_count) }}</span>
            <span class="stat">★ {{ character.collect_count || 0 }}</span>
          </div>
        </div>
      </div>

      <div class="content-body">
        <div class="info-card">
          <h3>角色简介</h3>
          <p class="description">{{ character.description || '暂无描述' }}</p>
        </div>

        <div v-if="character.personality" class="info-card">
          <h3>性格设定</h3>
          <p>{{ character.personality }}</p>
        </div>

        <div v-if="character.background" class="info-card">
          <h3>背景故事</h3>
          <p>{{ character.background }}</p>
        </div>

        <div v-if="tagList.length" class="info-card">
          <h3>标签</h3>
          <div class="tags-row">
            <TagBadge v-for="tag in tagList" :key="tag.id" :tag="tag" />
          </div>
        </div>
      </div>
    </div>
    <div v-else class="error-state">
      <p>角色卡不存在或已下架</p>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { characterApi } from '../api/character'
import TagBadge from '../components/TagBadge.vue'
import AppLayout from '../layouts/AppLayout.vue'

const route = useRoute()
const character = ref(null)
const loading = ref(true)

const tagList = computed(() => {
  if (!character.value || !character.value.tags) return []
  return character.value.tags.split(',').filter(t => t.trim()).map((name, i) => ({
    id: Math.abs(name.split('').reduce((h, c) => ((h << 5) - h) + c.charCodeAt(0), 0) & 0x7fffffff) % 900 + 100 + i,
    name: name.trim()
  }))
})

const formatViews = (num) => {
  const value = Number(num || 0)
  if (value >= 100000000) return `${(value / 100000000).toFixed(1)}亿`
  if (value >= 10000) return `${(value / 10000).toFixed(1)}万`
  return `${value}`
}

onMounted(async () => {
  try {
    const id = route.params.id
    const res = await characterApi.getDetail(id)
    character.value = res.data
  } catch (e) {
    console.error('Failed to load character:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.character-detail {
  max-width: 900px;
  margin: 0 auto;
}

.loading, .error-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-tertiary);
}

.cover-section {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--space-lg);
  aspect-ratio: 3/1;
  max-height: 300px;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  color: var(--text-tertiary);
  opacity: 0.3;
}

.cover-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 40px var(--space-xl) var(--space-lg);
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: #fff;
}

.cover-overlay h1 {
  margin: 0 0 var(--space-sm);
  font-size: var(--text-2xl);
  font-weight: 700;
}

.stats-row {
  display: flex;
  gap: var(--space-md);
  font-size: var(--text-sm);
  opacity: 0.85;
}

.content-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.info-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.info-card h3 {
  margin: 0 0 var(--space-sm);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.info-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: var(--text-sm);
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.tag {
  padding: 4px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}
</style>
