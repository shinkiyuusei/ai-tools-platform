<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  type: { type: String, default: 'info' },   // info | success | warning | error
  title: { type: String, default: '' },
  dismissible: { type: Boolean, default: true },
})

const emit = defineEmits(['dismiss'])

const visible = ref(false)

onMounted(() => {
  requestAnimationFrame(() => { visible.value = true })
})
</script>

<template>
  <div :class="['alert', `alert--${type}`, { 'alert--visible': visible }]">
    <div class="alert-icon">
      <template v-if="type === 'error'">✕</template>
      <template v-else-if="type === 'success'">✓</template>
      <template v-else-if="type === 'warning'">⚠</template>
      <template v-else>ℹ</template>
    </div>
    <div class="alert-content">
      <span v-if="title" class="alert-title">{{ title }}</span>
      <slot />
    </div>
    <button v-if="dismissible" class="alert-dismiss" @click="emit('dismiss')">&times;</button>
  </div>
</template>

<style scoped>
.alert {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  font-size: var(--text-sm);
  opacity: 0;
  transform: translateY(-4px);
  transition: all var(--transition-base);
  background: var(--bg-card);
}
.alert--visible {
  opacity: 1;
  transform: translateY(0);
}

.alert-icon {
  font-size: 12px;
  font-weight: 700;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}
.alert-content {
  flex: 1;
  color: var(--text-secondary);
  line-height: var(--leading-normal);
}
.alert-title {
  display: block;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.alert-dismiss {
  font-size: 16px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color var(--transition-fast);
  flex-shrink: 0;
}
.alert-dismiss:hover { color: var(--text-primary); }

/* --- Types --- */
.alert--info {
  border-color: rgba(123, 156, 191, 0.3);
}
.alert--info .alert-icon {
  background: rgba(123, 156, 191, 0.15);
  color: var(--color-misty-blue);
}

.alert--success {
  border-color: rgba(61, 107, 86, 0.3);
}
.alert--success .alert-icon {
  background: rgba(61, 107, 86, 0.15);
  color: var(--color-dark-green-soft);
}

.alert--warning {
  border-color: rgba(255, 193, 7, 0.3);
}
.alert--warning .alert-icon {
  background: rgba(255, 193, 7, 0.15);
  color: #ffc107;
}

.alert--error {
  border-color: rgba(200, 85, 84, 0.3);
}
.alert--error .alert-icon {
  background: rgba(200, 85, 84, 0.15);
  color: var(--color-crimson-soft);
}
</style>
