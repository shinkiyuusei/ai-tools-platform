<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)

const defaults = {
  contentMode: 'nsfw',
  sensoryDensity: 'high',
  pacingPreference: 'slow',
  powerIntensity: 'extreme',
  proseStyle: 'direct',
  wordCount: 1500,
}

const local = computed(() => ({ ...defaults, ...props.modelValue }))

function get(key) { return local.value[key] }
function set(key, val) {
  emit('update:modelValue', { ...local.value, [key]: val })
}

const densityOptions = [
  { value: 'low', label: '轻量', desc: '氛围暗示为主' },
  { value: 'medium', label: '均衡', desc: '五感轮流覆盖' },
  { value: 'high', label: '过载', desc: '感官密集轰炸' },
]
const pacingOptions = [
  { value: 'slow', label: '慢热', desc: '每次进出完整展开' },
  { value: 'balanced', label: '均衡', desc: '张弛有度' },
  { value: 'fast', label: '快节奏', desc: '高速冲刺为主' },
]
const powerOptions = [
  { value: 'mild', label: '温和', desc: '暧昧拉扯为主' },
  { value: 'medium', label: '标准', desc: '支配与臣服并重' },
  { value: 'extreme', label: '极限', desc: '推到支配极限' },
]

const isNsfw = computed(() => get('contentMode') === 'nsfw')
</script>

<template>
  <!-- Floating trigger button -->
  <button class="wsd-fab" @click="visible = !visible" :title="visible ? '关闭写作配置' : '写作风格配置'">
    <span class="wsd-fab-icon" :class="{ open: visible }">⚙</span>
  </button>

  <!-- Backdrop -->
  <Teleport to="body">
    <div v-if="visible" class="wsd-backdrop" @click.self="visible = false" />

    <!-- Drawer -->
    <div v-if="visible" class="wsd-drawer">
      <div class="wsd-header">
        <h3>写作风格配置</h3>
        <button class="wsd-close" @click="visible = false">×</button>
      </div>

      <div class="wsd-body">
        <!-- Group 1: Content Mode -->
        <div class="wsd-group">
          <div class="wsd-group-title">模式选择</div>

          <div class="wsd-field-row">
            <span class="wsd-label">内容模式</span>
            <div class="wsd-toggle-row">
              <span :class="{ active: !isNsfw }">正常</span>
              <button
                class="wsd-toggle"
                :class="{ on: isNsfw }"
                @click="set('contentMode', isNsfw ? 'normal' : 'nsfw')"
                role="switch"
                :aria-checked="isNsfw"
              >
                <span class="wsd-toggle-knob" />
              </button>
              <span :class="{ active: isNsfw }">NSFW</span>
            </div>
          </div>
          <p class="wsd-hint" v-if="isNsfw">
            NSFW 模式：启用感官过载轰炸、权力支配博弈、直白情色描写。叙事篇幅 ≥1500 字。
          </p>
          <p class="wsd-hint" v-else>
            正常模式：注重情节推进与角色塑造，适度的环境氛围渲染。叙事篇幅 ~800 字。
          </p>
        </div>

        <!-- Group 2: NSFW Tunables -->
        <div class="wsd-group" :class="{ disabled: !isNsfw }">
          <div class="wsd-group-title">
            NSFW 调参
            <span v-if="!isNsfw" class="wsd-disabled-badge">当前模式不可用</span>
          </div>

          <!-- Sensory Density -->
          <div class="wsd-field">
            <span class="wsd-label">感官密度</span>
            <div class="wsd-radio-group">
              <button
                v-for="o in densityOptions" :key="o.value"
                class="wsd-radio"
                :class="{ active: get('sensoryDensity') === o.value }"
                :disabled="!isNsfw"
                @click="set('sensoryDensity', o.value)"
              >
                <span class="wsd-radio-label">{{ o.label }}</span>
                <span class="wsd-radio-desc">{{ o.desc }}</span>
              </button>
            </div>
          </div>

          <!-- Pacing Preference -->
          <div class="wsd-field">
            <span class="wsd-label">叙事节奏</span>
            <div class="wsd-radio-group">
              <button
                v-for="o in pacingOptions" :key="o.value"
                class="wsd-radio"
                :class="{ active: get('pacingPreference') === o.value }"
                :disabled="!isNsfw"
                @click="set('pacingPreference', o.value)"
              >
                <span class="wsd-radio-label">{{ o.label }}</span>
                <span class="wsd-radio-desc">{{ o.desc }}</span>
              </button>
            </div>
          </div>

          <!-- Power Intensity -->
          <div class="wsd-field">
            <span class="wsd-label">支配强度</span>
            <div class="wsd-radio-group">
              <button
                v-for="o in powerOptions" :key="o.value"
                class="wsd-radio"
                :class="{ active: get('powerIntensity') === o.value }"
                :disabled="!isNsfw"
                @click="set('powerIntensity', o.value)"
              >
                <span class="wsd-radio-label">{{ o.label }}</span>
                <span class="wsd-radio-desc">{{ o.desc }}</span>
              </button>
            </div>
          </div>

          <!-- Prose Style -->
          <div class="wsd-field-row">
            <span class="wsd-label">文风倾向</span>
            <div class="wsd-toggle-row">
              <span :class="{ active: get('proseStyle') === 'literary' }">文学化</span>
              <button
                class="wsd-toggle"
                :class="{ on: get('proseStyle') === 'direct' }"
                :disabled="!isNsfw"
                @click="set('proseStyle', get('proseStyle') === 'direct' ? 'literary' : 'direct')"
                role="switch"
                :aria-checked="get('proseStyle') === 'direct'"
              >
                <span class="wsd-toggle-knob" />
              </button>
              <span :class="{ active: get('proseStyle') === 'direct' }">直白</span>
            </div>
          </div>

          <!-- Word Count -->
          <div class="wsd-field">
            <div class="wsd-label-row">
              <span class="wsd-label">目标字数</span>
              <span class="wsd-value">{{ get('wordCount') }} 字</span>
            </div>
            <div class="wsd-slider-wrap">
              <input
                type="range"
                class="wsd-slider"
                :min="isNsfw ? 1000 : 400"
                :max="isNsfw ? 3000 : 1500"
                :step="100"
                :value="get('wordCount')"
                :disabled="!isNsfw"
                @input="set('wordCount', Number($event.target.value))"
              />
              <div class="wsd-slider-ticks">
                <span>{{ isNsfw ? 1000 : 400 }}</span>
                <span>{{ isNsfw ? 3000 : 1500 }}</span>
              </div>
            </div>
            <p class="wsd-hint">
              {{ isNsfw ? 'NSFW 推荐 1500 字以上，确保叙事、状态栏、抉择分支完整输出。' : '正常模式推荐 800 字左右。' }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* ====== FAB ====== */
.wsd-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 900;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  background: var(--bg-card, #1a1d2e);
  color: var(--text-tertiary, #8892a0);
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s ease;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
.wsd-fab:hover {
  color: #f0a040;
  border-color: #f0a040;
  transform: scale(1.08);
  box-shadow: 0 4px 20px rgba(240, 160, 64, 0.2);
}
.wsd-fab-icon {
  display: inline-block;
  transition: transform 0.4s ease;
}
.wsd-fab-icon.open {
  transform: rotate(90deg);
}

/* ====== Backdrop ====== */
.wsd-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.35);
}

/* ====== Drawer ====== */
.wsd-drawer {
  position: fixed;
  top: 0;
  right: 0;
  z-index: 1001;
  width: 420px;
  max-width: 92vw;
  height: 100vh;
  overflow-y: auto;
  background: var(--bg-card, #1a1d2e);
  border-left: 1px solid var(--border-card, rgba(255,255,255,0.08));
  box-shadow: -4px 0 32px rgba(0,0,0,0.4);
  animation: slideIn 0.25s ease;
}
@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

/* ====== Header ====== */
.wsd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-card, rgba(255,255,255,0.08));
  position: sticky;
  top: 0;
  background: var(--bg-card, #1a1d2e);
  z-index: 1;
}
.wsd-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #e2e8f0);
}
.wsd-close {
  width: 32px; height: 32px;
  border: none;
  background: transparent;
  color: var(--text-tertiary, #8892a0);
  font-size: 22px;
  cursor: pointer;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.wsd-close:hover { color: var(--text-primary, #e2e8f0); background: rgba(255,255,255,0.06); }

/* ====== Body ====== */
.wsd-body {
  padding: 16px 20px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ====== Groups ====== */
.wsd-group {
  background: var(--bg-elevated, rgba(255,255,255,0.03));
  border: 1px solid var(--border-card, rgba(255,255,255,0.06));
  border-radius: 10px;
  padding: 16px;
  transition: opacity 0.2s;
}
.wsd-group.disabled {
  opacity: 0.45;
  pointer-events: none;
}
.wsd-group-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #a0aec0);
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-card, rgba(255,255,255,0.06));
  display: flex; align-items: center; gap: 10px;
}
.wsd-disabled-badge {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-tertiary, #8892a0);
  background: rgba(255,255,255,0.05);
  padding: 2px 8px;
  border-radius: 4px;
}

/* ====== Fields ====== */
.wsd-field { margin-bottom: 14px; }
.wsd-field:last-child { margin-bottom: 0; }
.wsd-field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.wsd-field-row:last-child { margin-bottom: 0; }
.wsd-label {
  font-size: 13px;
  color: var(--text-secondary, #a0aec0);
}
.wsd-label-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.wsd-value {
  font-size: 13px; font-weight: 600; color: #f0a040;
}
.wsd-hint {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--text-tertiary, #8892a0);
  line-height: 1.5;
}

/* ====== Toggle ====== */
.wsd-toggle-row {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: var(--text-tertiary, #8892a0);
}
.wsd-toggle-row span.active { color: var(--text-primary, #e2e8f0); font-weight: 600; }
.wsd-toggle {
  width: 44px; height: 24px;
  border-radius: 12px;
  border: none;
  background: var(--bg-tertiary, rgba(255,255,255,0.08));
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}
.wsd-toggle.on { background: #f0a040; }
.wsd-toggle:disabled { opacity: 0.5; cursor: not-allowed; }
.wsd-toggle-knob {
  position: absolute;
  top: 2px; left: 2px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.wsd-toggle.on .wsd-toggle-knob { transform: translateX(20px); }

/* ====== Radio Group ====== */
.wsd-radio-group {
  display: flex; gap: 6px; margin-top: 6px;
}
.wsd-radio {
  flex: 1;
  padding: 8px 6px;
  border-radius: 8px;
  border: 1px solid var(--border-card, rgba(255,255,255,0.08));
  background: transparent;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.wsd-radio:hover:not(:disabled):not(.active) {
  border-color: rgba(240, 160, 64, 0.3);
  background: rgba(240, 160, 64, 0.05);
}
.wsd-radio.active {
  border-color: #f0a040;
  background: rgba(240, 160, 64, 0.1);
}
.wsd-radio:disabled { cursor: not-allowed; opacity: 0.5; }
.wsd-radio-label {
  font-size: 12px; font-weight: 600;
  color: var(--text-secondary, #a0aec0);
}
.wsd-radio.active .wsd-radio-label { color: #f0a040; }
.wsd-radio-desc {
  font-size: 10px;
  color: var(--text-tertiary, #8892a0);
  display: none;
}
.wsd-radio.active .wsd-radio-desc { display: block; }

/* ====== Slider ====== */
.wsd-slider-wrap { margin-top: 4px; }
.wsd-slider {
  width: 100%; height: 6px;
  -webkit-appearance: none; appearance: none;
  background: var(--bg-tertiary, rgba(255,255,255,0.08));
  border-radius: 3px; outline: none;
}
.wsd-slider:disabled { opacity: 0.5; }
.wsd-slider::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: #f0a040; cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.wsd-slider-ticks {
  display: flex; justify-content: space-between;
  font-size: 10px; color: var(--text-tertiary, #8892a0); margin-top: 2px;
}
</style>
