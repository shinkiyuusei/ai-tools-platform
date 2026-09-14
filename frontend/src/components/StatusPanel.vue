<script setup>
import { computed, ref, watch } from 'vue'
import { buildStatusCharacters } from '../utils/statusPanel'

const props = defineProps({
  statusData: { type: Object, default: null },
  schema: { type: [Array, Object], default: () => ({}) },
})

// Track collapsed state per character name
const collapsed = ref({})

// Reset collapsed state when schema or statusData changes
watch(() => [props.schema, props.statusData], () => {
  collapsed.value = {}
}, { deep: true })

const characters = computed(() => buildStatusCharacters(props.schema, props.statusData))

function toggleCollapse(name) {
  const key = name || '_single'
  collapsed.value[key] = !collapsed.value[key]
}

function isCollapsed(name) {
  const key = name || '_single'
  return !!collapsed.value[key]
}

function effectiveFields(char) {
  if (!char.fields?.length) return []
  return char.fields.filter((f) => {
    const val = char.data?.[f.key]
    return val !== undefined && val !== null
  })
}

function formatValue(field, char) {
  const entry = char.data?.[field.key]
  if (!entry) return '—'
  if (field.type === 'number' && typeof entry === 'object' && entry.type === 'number') {
    let display = String(entry.value)
    if (entry.delta !== 0) {
      const sign = entry.delta > 0 ? '+' : ''
      display += ` (${sign}${entry.delta})`
    }
    return display
  }
  // Text values are stored directly or as { value, raw, type: 'text' }
  if (typeof entry === 'object') {
    return entry.raw || entry.value || '—'
  }
  return entry
}

function valueClass(field, char) {
  const entry = char.data?.[field.key]
  if (!entry || field.type !== 'number') return 'text'
  if (typeof entry !== 'object' || entry.type !== 'number') return 'text'
  if (entry.delta > 0) return 'number up'
  if (entry.delta < 0) return 'number down'
  return 'number'
}
</script>

<template>
  <div v-if="characters.length" class="status-panel">
    <template v-for="char in characters" :key="char.name || '_single'">
      <section class="status-section">
        <button
          v-if="char.name"
          type="button"
          class="status-char-name"
          :class="{ collapsed: isCollapsed(char.name) }"
          @click="toggleCollapse(char.name)"
        >
          <span class="status-icon">◆</span>
          <span class="character-name">{{ char.name }}</span>
          <span class="field-count">{{ effectiveFields(char).length }} 项</span>
          <span class="collapse-arrow">{{ isCollapsed(char.name) ? '展开' : '收起' }}</span>
        </button>
        <div v-else class="status-overview">
          <span class="status-icon">◆</span>
          <span>当前状态</span>
          <span class="field-count">{{ effectiveFields(char).length }} 项</span>
        </div>
        <div class="status-fields" :class="{ collapsed: char.name && isCollapsed(char.name) }">
          <div v-for="field in effectiveFields(char)" :key="field.key" class="status-field">
            <span class="status-label">{{ field.label }}</span>
            <span class="status-value" :class="valueClass(field, char)">{{ formatValue(field, char) }}</span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.status-panel {
  width: min(100%, 430px);
  margin-top: 12px;
  padding: 10px;
  color: var(--text-primary, #eef0ff);
  background: linear-gradient(145deg, rgba(37, 40, 62, 0.92), rgba(24, 26, 42, 0.92));
  border: 1px solid rgba(151, 162, 226, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(5, 7, 20, 0.2);
  font-size: 12px;
}

.status-section + .status-section { margin-top: 8px; }

.status-char-name {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 9px;
  color: #e9ebff;
  font: inherit;
  font-weight: 600;
  text-align: left;
  background: rgba(116, 125, 188, 0.13);
  border: 1px solid rgba(152, 163, 232, 0.16);
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.status-char-name:hover {
  background: rgba(128, 141, 211, 0.22);
  border-color: rgba(164, 176, 249, 0.3);
}

.status-overview {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 2px 9px;
  color: #e9ebff;
  font-weight: 600;
}

.collapse-arrow {
  margin-left: 4px;
  color: #9ea6d5;
  font-size: 11px;
  font-weight: 400;
}

.character-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.field-count {
  margin-left: auto;
  color: #9ea6d5;
  font-size: 10px;
  font-weight: 400;
  white-space: nowrap;
}

.status-icon {
  color: #aeb9ff;
  font-size: 9px;
}

.status-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  margin-top: 7px;
  overflow: hidden;
  transition: max-height 0.22s ease, opacity 0.16s ease, margin 0.16s ease;
  max-height: 800px;
  opacity: 1;
}

.status-fields.collapsed {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
}

.status-field {
  min-width: 0;
  padding: 7px 8px;
  background: rgba(8, 10, 24, 0.26);
  border: 1px solid rgba(151, 162, 226, 0.1);
  border-radius: 7px;
}

.status-label {
  display: block;
  margin-bottom: 3px;
  color: #9ea6d5;
  font-size: 10px;
  white-space: nowrap;
}

.status-value {
  display: block;
  color: #e7e9f8;
  line-height: 1.45;
  word-break: break-word;
}

.status-value.text {
  color: #e7e9f8;
}

.status-value.number {
  color: #c8d0ff;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.status-value.number.up {
  color: #82d5a0;
}

.status-value.number.down {
  color: #ff9bad;
}

@media (max-width: 420px) {
  .status-fields { grid-template-columns: 1fr; }
}
</style>
