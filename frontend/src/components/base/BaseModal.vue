<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  size: { type: String, default: 'md' },   // sm | md | lg
  closable: { type: Boolean, default: true },
})

const emit = defineEmits(['close'])

const modalRef = ref(null)
const visible = ref(false)

function close() {
  if (props.closable) {
    visible.value = false
    setTimeout(() => emit('close'), 250)
  }
}

function onKeydown(e) {
  if (e.key === 'Escape') close()
}

function onClickBackdrop(e) {
  if (e.target === modalRef.value) close()
}

onMounted(() => {
  requestAnimationFrame(() => { visible.value = true })
  document.addEventListener('keydown', onKeydown)
  document.body.style.overflow = 'hidden'
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div
      ref="modalRef"
      class="modal-backdrop"
      :class="{ 'modal--visible': visible }"
      @click="onClickBackdrop"
    >
      <div :class="['modal-panel', `modal-panel--${size}`]">
        <div v-if="title || closable" class="modal-header">
          <h3 v-if="title" class="modal-title">{{ title }}</h3>
          <button v-if="closable" class="modal-close" @click="close">&times;</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="modal-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  opacity: 0;
  transition: opacity var(--transition-base);
}
.modal--visible {
  opacity: 1;
}

.modal-panel {
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  transform: translateY(12px) scale(0.97);
  transition: transform var(--transition-base);
}
.modal--visible .modal-panel {
  transform: translateY(0) scale(1);
}

.modal-panel--sm { width: 400px; }
.modal-panel--md { width: 560px; }
.modal-panel--lg { width: 760px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-lg) 0;
  flex-shrink: 0;
}
.modal-title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin: 0;
}
.modal-close {
  font-size: 20px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  line-height: 1;
}
.modal-close:hover {
  color: var(--text-primary);
  background: var(--bg-card);
}

.modal-body {
  padding: var(--space-lg);
  overflow-y: auto;
  flex: 1;
}
.modal-footer {
  padding: 0 var(--space-lg) var(--space-lg);
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .modal-panel--sm, .modal-panel--md, .modal-panel--lg {
    width: 100%;
  }
  .modal-backdrop {
    padding: var(--space-md);
  }
}
</style>
