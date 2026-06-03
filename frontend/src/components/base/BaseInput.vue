<script setup>
import { useId } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  label: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'enter'])
const id = useId()

const onInput = (event) => {
  emit('update:modelValue', event.target.value)
}
</script>

<template>
  <div class="base-input-wrap">
    <label v-if="label" :for="id" class="base-input-label">{{ label }}</label>
    <input
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="base-input"
      :class="{ 'base-input--error': error }"
      @input="onInput"
      @keyup.enter="$emit('enter')"
    />
    <span v-if="error" class="base-input-error">{{ error }}</span>
  </div>
</template>

<style scoped>
.base-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.base-input-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
}

.base-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
}

.base-input::placeholder {
  color: var(--text-tertiary);
}

.base-input:hover:not(:disabled) {
  border-color: var(--text-tertiary);
}

.base-input:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(123, 156, 191, 0.1);
}

.base-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.base-input--error {
  border-color: var(--color-crimson);
}

.base-input--error:focus {
  box-shadow: 0 0 0 3px rgba(200, 85, 84, 0.1);
}

.base-input-error {
  font-size: var(--text-xs);
  color: var(--color-crimson-soft);
}
</style>
