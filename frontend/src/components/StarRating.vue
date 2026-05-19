<template>
  <div class="star-rating" :class="{ readonly: !interactive }">
    <button
      v-for="s in 5"
      :key="s"
      :class="['star', { active: s <= displayScore, half: halfStar === s }]"
      :disabled="!interactive || submitting"
      @click="rate(s)"
      @mouseenter="hovered = s"
      @mouseleave="hovered = null"
      :title="interactive ? `${s} 星` : `${average} 分（${count} 人评价）`"
    >★</button>
    <span v-if="count >= 0" class="rating-text">{{ average > 0 ? average.toFixed(1) : '-' }}</span>
    <span v-if="showLoginHint" class="login-hint">请先登录</span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ratingApi } from '../api/rating'

const router = useRouter()

const props = defineProps({
  workType: { type: String, required: true },
  workId: { type: Number, required: true },
  interactive: { type: Boolean, default: true },
})

const myScore = ref(0)
const average = ref(0)
const count = ref(0)
const submitting = ref(false)
const hovered = ref(null)
const showLoginHint = ref(false)

const displayScore = computed(() => hovered.value || myScore.value)
const halfStar = computed(() => 0)

const hasToken = () => !!localStorage.getItem('token')

const fetchRating = async () => {
  try {
    const res = await ratingApi.get(props.workType, props.workId)
    average.value = res.data.average || 0
    count.value = res.data.count || 0
    myScore.value = res.data.myScore || 0
  } catch (e) {
    // silent
  }
}

const rate = async (score) => {
  if (!props.interactive || submitting.value) return
  if (!hasToken()) {
    showLoginHint.value = true
    setTimeout(() => { showLoginHint.value = false }, 2000)
    return
  }
  submitting.value = true
  try {
    await ratingApi.submit(props.workType, props.workId, score)
    myScore.value = score
    await fetchRating()
  } catch (e) {
    const status = e?.response?.status
    if (status === 401) {
      showLoginHint.value = true
      setTimeout(() => { showLoginHint.value = false }, 2000)
    }
  } finally {
    submitting.value = false
  }
}

onMounted(fetchRating)
</script>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  position: relative;
}

.star {
  background: none;
  border: none;
  font-size: 18px;
  color: #444;
  cursor: pointer;
  padding: 0 1px;
  transition: color 0.15s, transform 0.15s;
  line-height: 1;
}

.star.active {
  color: #f0a040;
}

.star:hover:not(:disabled) {
  transform: scale(1.2);
  color: #f5c060;
}

.star:disabled {
  cursor: default;
}

.readonly .star {
  cursor: default;
  font-size: 15px;
}

.rating-text {
  font-size: 13px;
  color: #f0a040;
  font-weight: 600;
  margin-left: 6px;
  min-width: 28px;
}

.login-hint {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  background: #c85554;
  color: #fff;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  animation: fadeInOut 2s ease;
}

@keyframes fadeInOut {
  0% { opacity: 0; transform: translateX(-50%) translateY(4px); }
  15% { opacity: 1; transform: translateX(-50%) translateY(0); }
  75% { opacity: 1; }
  100% { opacity: 0; }
}
</style>
