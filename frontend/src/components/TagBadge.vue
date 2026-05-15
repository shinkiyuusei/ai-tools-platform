<script setup>
defineProps({
  tag: { type: Object, required: true },
})

const emit = defineEmits(['tag-click'])

const colorNames = ['misty', 'crimson', 'candy', 'green', 'silver', 'pale']

function tagColorClass(tagId) {
  return `tag--${colorNames[(tagId - 1) % colorNames.length]}`
}
</script>

<template>
  <span
    :class="['tag-badge', tagColorClass(tag.id)]"
    @click.stop="emit('tag-click', tag.id)"
  >{{ tag.name }}</span>
</template>

<style scoped>
.tag-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.5;
  white-space: nowrap;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}
.tag-badge:hover {
  opacity: 0.75;
}

.tag--misty  { background: rgba(123, 156, 191, 0.15); color: var(--color-misty-blue-soft); }
.tag--crimson { background: rgba(200, 85, 84, 0.15); color: var(--color-crimson-soft); }
.tag--candy  { background: rgba(238, 162, 180, 0.15); color: var(--color-candy-pink-soft); }
.tag--green  { background: rgba(61, 107, 86, 0.15); color: var(--color-dark-green-soft); }
.tag--silver { background: rgba(158, 158, 170, 0.15); color: var(--color-silver-gray-soft); }
.tag--pale   { background: rgba(226, 217, 207, 0.10); color: var(--color-pale-soft); }
</style>
