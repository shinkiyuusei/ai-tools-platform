<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  statusData: { type: Object, default: null },
  schema: { type: [Array, Object], default: () => ({}) },
})

// Detect single-character (schema is Array) vs multi-character (schema is Object)
const isMultiChar = computed(() => {
  return props.schema && !Array.isArray(props.schema)
})

// Track collapsed state per character name
const collapsed = ref({})

// Reset collapsed state when schema or statusData changes
watch(() => [props.schema, props.statusData], () => {
  collapsed.value = {}
}, { deep: true })

// Build list of { name, fields } entries for rendering.
// Uses statusData keys as the primary character list (matching AI output),
// falling back to schema keys, so name mismatches between schema and AI
// output are handled gracefully.
const characters = computed(() => {
  if (!props.schema) return []
  if (isMultiChar.value) {
    const dataNames = props.statusData ? Object.keys(props.statusData) : []
    const schemaNames = Object.keys(props.schema)
    // Merge: statusData names first (AI output), then any schema-only names
    const allNames = [...new Set([...dataNames, ...schemaNames])]
    return allNames.map((name) => ({
      name,
      // Use matching schema entry if exists, otherwise fall back to any available schema
      fields: props.schema[name] || Object.values(props.schema)[0] || [],
      data: props.statusData?.[name] || {},
    }))
  }
  // Single-character: schema = [fields], statusData = { fieldKey: value }
  return [{
    name: null,
    fields: props.schema || [],
    data: props.statusData || {},
  }]
})

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
      <!-- Character name header (multi-character only) — clickable to toggle collapse -->
      <div
        v-if="char.name"
        class="status-char-name"
        :class="{ collapsed: isCollapsed(char.name) }"
        @click="toggleCollapse(char.name)"
      >
        <span class="collapse-arrow">{{ isCollapsed(char.name) ? '▸' : '▾' }}</span>
        <span class="status-icon">◆</span>
        <span>{{ char.name }}</span>
      </div>
      <!-- Single-character toggle header -->
      <div
        v-else
        class="status-char-name single-toggle"
        :class="{ collapsed: isCollapsed(null) }"
        @click="toggleCollapse(null)"
      >
        <span class="collapse-arrow">{{ isCollapsed(null) ? '▸' : '▾' }}</span>
        <span class="status-label-hint">状态栏</span>
        <span class="field-count">{{ effectiveFields(char).length }} 项</span>
      </div>
      <!-- Fields (collapsible) -->
      <div
        class="status-fields"
        :class="{ collapsed: isCollapsed(char.name) }"
      >
        <div
          v-for="field in effectiveFields(char)"
          :key="field.key"
          class="status-field"
        >
          <span class="status-label">{{ field.label }}</span>
          <span class="status-value" :class="valueClass(field, char)">
            {{ formatValue(field, char) }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.status-panel {
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(37, 37, 56, 0.5);
  border: 1px solid var(--border-card, rgba(100, 100, 140, 0.2));
  border-radius: var(--radius-md, 6px);
  font-size: 12px;
  max-width: 340px;
}

.status-char-name {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary, #ccc);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin-top: 6px;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  user-select: none;
  transition: color var(--transition-fast, 0.15s);
}

.status-char-name:hover {
  color: var(--text-primary, #eee);
}

.status-char-name.collapsed {
  border-bottom-color: transparent;
  margin-bottom: 0;
}

.status-char-name:first-child {
  margin-top: 0;
}

/* Single-character toggle header */
.status-char-name.single-toggle {
  font-weight: 500;
  font-size: 10px;
  color: var(--text-tertiary, #888);
  margin-top: 0;
  margin-bottom: 4px;
}

.status-char-name.single-toggle.collapsed {
  margin-bottom: 0;
  border-bottom-color: transparent;
}

.collapse-arrow {
  font-size: 10px;
  color: var(--text-tertiary, #888);
  transition: transform var(--transition-fast, 0.15s);
  flex-shrink: 0;
  width: 10px;
  text-align: center;
}

.status-char-name:hover .collapse-arrow {
  color: var(--text-primary, #eee);
}

.status-label-hint {
  color: var(--text-tertiary, #888);
  font-weight: 400;
}

.field-count {
  font-weight: 400;
  color: var(--text-tertiary, #888);
  font-size: 10px;
  margin-left: auto;
}

.status-icon {
  color: var(--color-candy-pink-soft, #e895a8);
  font-size: 8px;
}

.status-fields {
  display: flex;
  flex-direction: column;
  margin-bottom: 2px;
  overflow: hidden;
  transition: max-height 0.25s ease, opacity 0.2s ease, margin 0.2s ease;
  max-height: 600px;
  opacity: 1;
}

.status-fields.collapsed {
  max-height: 0;
  opacity: 0;
  margin-bottom: 0;
}

.status-field {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 2px 0;
  gap: 12px;
}

.status-field:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.status-label {
  color: var(--text-tertiary, #888);
  flex-shrink: 0;
  white-space: nowrap;
}

.status-value {
  text-align: right;
  word-break: break-word;
}

.status-value.text {
  color: var(--text-secondary, #aaa);
}

.status-value.number {
  color: var(--color-candy-pink-soft, #e895a8);
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}

.status-value.number.up {
  color: #7ecb8a;
}

.status-value.number.down {
  color: #e895a8;
}
</style>
