<template>
  <AppLayout>
    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="character" class="character-detail animate-fade-in">
      <div class="cover-section">
        <img v-if="character.avatar" :src="character.avatar" :alt="character.name" class="cover-img" />
        <div v-else class="cover-placeholder">{{ character.name.slice(0, 2) }}</div>
        <div class="cover-overlay">
          <div class="cover-top">
            <h1>{{ character.name }}</h1>
            <p class="author" v-if="character.author">— {{ character.author }}</p>
          </div>
          <div class="stats-row">
            <span class="stat">♥ {{ character.likeCount || 0 }}</span>
            <span class="stat">👁 {{ character.viewCount || 0 }}</span>
            <span class="stat">★ {{ character.collectCount || 0 }}</span>
            <span class="stat">💬 {{ character.useCount || 0 }}</span>
          </div>
        </div>
      </div>

      <div class="actions-bar">
        <button class="btn-chat" @click="startChat">{{ t('character.start_chat') }}</button>
        <button class="btn-like" @click="toggleLike">
          {{ liked ? '♥' : '♡' }} {{ character.likeCount || 0 }}
        </button>
        <button class="btn-collect" @click="toggleCollect">
          {{ collected ? '★' : '☆' }} {{ character.collectCount || 0 }}
        </button>
      </div>

      <div class="content-body">
        <div v-if="character.desc" class="info-card">
          <h3>{{ t('character.desc') }}</h3>
          <p>{{ character.desc }}</p>
        </div>

        <div v-if="tagList.length" class="info-card">
          <h3>{{ t('character.tags') }}</h3>
          <div class="tags-row">
            <span v-for="(tag, i) in tagList" :key="i" class="tag">{{ tag }}</span>
          </div>
        </div>

        <div v-if="character.personaContent" class="info-card">
          <h3>{{ t('character.persona_content') }}</h3>
          <div class="persona-content" v-text="character.personaContent"></div>
        </div>
      </div>
    </div>
    <div v-else class="error-state">
      <p>{{ t('character.not_found') }}</p>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { characterApi } from '../api/character'
import AppLayout from '../layouts/AppLayout.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const character = ref(null)
const loading = ref(true)
const liked = ref(false)
const collected = ref(false)

const tagList = computed(() => {
  if (!character.value || !character.value.tags) return []
  return Array.isArray(character.value.tags) ? character.value.tags : []
})

const startChat = () => {
  router.push(`/chat/character/${character.value.id}`)
}

const toggleLike = async () => {
  try {
    const res = await characterApi.like(character.value.id)
    liked.value = res.data.liked
    character.value.likeCount += res.data.liked ? 1 : -1
  } catch (e) { /* ignore */ }
}

const toggleCollect = async () => {
  try {
    const res = await characterApi.collect(character.value.id)
    collected.value = res.data.collected
    character.value.collectCount += res.data.collected ? 1 : -1
  } catch (e) { /* ignore */ }
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
  margin-bottom: var(--space-md);
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

.cover-top {
  margin-bottom: var(--space-sm);
}

.cover-overlay h1 {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: 700;
}

.author {
  margin: 4px 0 0;
  font-size: var(--text-sm);
  opacity: 0.7;
}

.stats-row {
  display: flex;
  gap: var(--space-md);
  font-size: var(--text-sm);
  opacity: 0.85;
}

.actions-bar {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.btn-chat, .btn-like, .btn-collect {
  padding: 8px 20px;
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: 500;
  background: var(--bg-card);
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.btn-chat {
  background: var(--color-misty-blue-deep);
  color: #fff;
  border-color: transparent;
}

.btn-chat:hover {
  background: var(--color-misty-blue);
}

.btn-like:hover, .btn-collect:hover {
  border-color: var(--border-primary);
  background: var(--bg-elevated);
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

.persona-content {
  white-space: pre-wrap;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: var(--space-md);
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
