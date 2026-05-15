<script setup>
import { computed } from 'vue'

const props = defineProps({
  pageNum: { type: Number, required: true },
  pageSize: { type: Number, required: true },
  total: { type: Number, required: true },
})
const emit = defineEmits(['update:page-num'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const pages = computed(() => {
  const current = props.pageNum
  const total = totalPages.value
  const result = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) result.push(i)
  } else {
    result.push(1)
    if (current > 3) result.push('...')
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
      result.push(i)
    }
    if (current < total - 2) result.push('...')
    result.push(total)
  }
  return result
})

const changePage = (page) => {
  if (page < 1 || page > totalPages.value || page === props.pageNum) return
  emit('update:page-num', page)
}
</script>

<template>
  <div v-if="totalPages > 1" class="base-pagination">
    <button
      class="page-btn"
      :disabled="pageNum <= 1"
      @click="changePage(pageNum - 1)"
    >‹</button>
    <template v-for="(p, idx) in pages" :key="idx">
      <span v-if="p === '...'" class="page-ellipsis">…</span>
      <button
        v-else
        class="page-btn"
        :class="{ active: p === pageNum }"
        @click="changePage(p)"
      >{{ p }}</button>
    </template>
    <button
      class="page-btn"
      :disabled="pageNum >= totalPages"
      @click="changePage(pageNum + 1)"
    >›</button>
    <span class="page-total">共 {{ total }} 项</span>
  </div>
</template>

<style scoped>
.base-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: var(--space-lg) 0;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled):not(.active) {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-primary);
}

.page-btn.active {
  background: var(--color-misty-blue-deep);
  color: #fff;
  border-color: var(--color-misty-blue-deep);
  font-weight: 600;
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-ellipsis {
  color: var(--text-tertiary);
  padding: 0 4px;
}

.page-total {
  margin-left: var(--space-md);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
</style>
