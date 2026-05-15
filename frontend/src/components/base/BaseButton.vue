<script setup>
defineProps({
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' },
  block: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  size: { type: String, default: 'md' },
})
</script>

<template>
  <button
    class="base-button"
    :class="[
      `base-button--${variant}`,
      `base-button--${size}`,
      { 'base-button--block': block, 'base-button--loading': loading }
    ]"
    :type="type"
    :disabled="loading"
  >
    <span v-if="loading" class="loading-dot">⟳</span>
    <slot v-else />
  </button>
</template>

<style scoped>
.base-button {
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  letter-spacing: 0.02em;
  position: relative;
  overflow: hidden;
}

.base-button--sm {
  padding: 6px 14px;
  font-size: var(--text-xs);
  border-radius: var(--radius-sm);
}

.base-button--md {
  padding: 10px 20px;
  font-size: var(--text-sm);
}

.base-button--lg {
  padding: 14px 28px;
  font-size: var(--text-base);
  border-radius: var(--radius-lg);
}

.base-button--block {
  width: 100%;
}

.base-button--primary {
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-misty-blue));
  color: #fff;
  box-shadow: 0 2px 8px rgba(123, 156, 191, 0.2);
}

.base-button--primary:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(123, 156, 191, 0.35);
  transform: translateY(-1px);
}

.base-button--secondary {
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-primary);
}

.base-button--secondary:hover:not(:disabled) {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-color: var(--border-focus);
}

.base-button--danger {
  background: rgba(200, 85, 84, 0.12);
  color: var(--color-crimson-soft);
  border: 1px solid rgba(200, 85, 84, 0.2);
}

.base-button--danger:hover:not(:disabled) {
  background: rgba(200, 85, 84, 0.2);
  border-color: var(--color-crimson);
}

.base-button--ghost {
  background: transparent;
  color: var(--text-secondary);
}

.base-button--ghost:hover:not(:disabled) {
  color: var(--text-primary);
  background: var(--bg-card);
}

.base-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.base-button--loading .loading-dot {
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
