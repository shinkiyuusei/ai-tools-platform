<script setup>
import { ref, computed, onUnmounted } from 'vue'

const props = defineProps({
  text: { type: String, required: true },
})

const visible = ref(false)
const x = ref(0)
const y = ref(0)
const triggerRef = ref(null)
let showTimer = null

const tooltipStyle = computed(() => ({
  left: `${x.value + 10}px`,
  top: `${y.value + 16}px`,
}))

function onEnter(e) {
  const child = triggerRef.value?.firstElementChild
  if (!child) return
  if (child.scrollWidth <= child.clientWidth + 1) return
  showTimer = setTimeout(() => {
    visible.value = true
    x.value = e.clientX
    y.value = e.clientY
  }, 200)
}

function onMove(e) {
  if (!visible.value) return
  x.value = e.clientX
  y.value = e.clientY
}

function onLeave() {
  clearTimeout(showTimer)
  visible.value = false
}

onUnmounted(() => clearTimeout(showTimer))
</script>

<template>
  <span
    ref="triggerRef"
    class="base-tooltip-trigger"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @mousemove="onMove"
  >
    <slot />
  </span>
  <Teleport to="body">
    <div v-if="visible" class="base-tooltip-popup" :style="tooltipStyle">
      {{ text }}
    </div>
  </Teleport>
</template>

<style scoped>
.base-tooltip-trigger {
  display: block;
  max-width: 100%;
}
</style>

<style>
.base-tooltip-popup {
  position: fixed;
  z-index: 10000;
  max-width: 400px;
  padding: 10px 16px;
  background: var(--bg-card, #1a1a2e);
  color: var(--text-primary, #e8e8e8);
  border: 1px solid var(--border-primary, rgba(255, 255, 255, 0.12));
  border-radius: var(--radius-md, 8px);
  font-size: var(--text-sm, 13px);
  line-height: 1.6;
  word-break: break-word;
  white-space: normal;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  pointer-events: none;
  user-select: none;
}
</style>
