<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chatApi } from '../api/chat'
import { notifySuccess, notifyError } from '../utils/notify';
import { characterApi } from '../api/character'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/base/BaseButton.vue'
import BaseInput from '../components/base/BaseInput.vue'
import AppLayout from '../layouts/AppLayout.vue'
import WritingStyleDrawer from '../components/WritingStyleDrawer.vue'

const router = useRouter()
const route = useRoute()
const saving = ref(false)
const isEdit = ref(false)
const editingWorkId = ref(null)
const uploading = ref(false)
const activeSection = ref('basic')
const createMode = ref('work') // 'work' | 'character'
const characterSaving = ref(false)
const characterUploading = ref(false)
const tagInput = ref('')

const characterForm = reactive({
  name: '',
  desc: '',
  avatar: '',
  tags: [],
  personaContent: '',
})

const form = reactive({
  name: '',
  desc: '',
  detailedIntro: '',
  icon: '',
  characters: [],
  protagonist: { name: '', description: '', motivation: '' },
  worldSetting: { worldName: '', eraTech: '', coreConflict: '', toneAtmosphere: '', mainPlot: '', initialState: '' },
  gameRules: '',
  statusBar: '',
  openings: [{ label: '', text: '' }],
  writingStyle: { contentMode: 'nsfw', sensoryDensity: 'high', pacingPreference: 'slow', powerIntensity: 'extreme', proseStyle: 'direct', wordCount: 1500 },
  aiProvider: 'deepseek',
})

const EMPTY_WORK_FORM = {
  name: '', desc: '', detailedIntro: '', icon: '', characters: [],
  protagonist: { name: '', description: '', motivation: '' },
  worldSetting: { worldName: '', eraTech: '', coreConflict: '', toneAtmosphere: '', mainPlot: '', initialState: '' },
  gameRules: '', statusBar: '', openings: [{ label: '', text: '' }],
  writingStyle: { contentMode: 'nsfw', sensoryDensity: 'high', pacingPreference: 'slow', powerIntensity: 'extreme', proseStyle: 'direct', wordCount: 1500 },
  aiProvider: 'deepseek',
}

const EMPTY_CHARACTER_FORM = {
  name: '', desc: '', avatar: '', tags: [], personaContent: '',
}

function resetWorkForm() {
  Object.assign(form, JSON.parse(JSON.stringify(EMPTY_WORK_FORM)))
}

function resetCharacterForm() {
  Object.assign(characterForm, JSON.parse(JSON.stringify(EMPTY_CHARACTER_FORM)))
}

async function fetchWorkForEdit(workId) {
  try {
    const res = await chatApi.getWorkConfig(workId)
    const w = res.data
    form.name = w.name || ''
    form.desc = w.desc || ''
    form.detailedIntro = w.detailedIntro || ''
    form.icon = w.icon || ''
    form.characters = (w.characters || []).map(c => ({
      name: c.name || '',
      occupation: c.occupation || '',
      age: c.age || '',
      gender: c.gender || '',
      appearance: c.appearance || '',
      personality: c.personality || '',
      speechTone: c.speechTone || '',
      background: c.background || '',
    }))
    form.protagonist = {
      name: w.protagonist?.name || '',
      description: w.protagonist?.description || '',
      motivation: w.protagonist?.motivation || '',
    }
    form.worldSetting = {
      worldName: w.worldSetting?.worldName || '',
      eraTech: w.worldSetting?.eraTech || '',
      coreConflict: w.worldSetting?.coreConflict || '',
      toneAtmosphere: w.worldSetting?.toneAtmosphere || '',
      mainPlot: w.worldSetting?.mainPlot || '',
      initialState: w.worldSetting?.initialState || '',
    }
    form.gameRules = w.gameRules || ''
    form.statusBar = w.statusBar || ''
    if (w.writingStyle) {
      form.writingStyle = { ...form.writingStyle, ...w.writingStyle }
    }
    const openings = w.openingStatements || []
    form.openings = openings.length ? openings.map(o => ({ label: o.label || '', text: o.text || '' })) : [{ label: '', text: '' }]
  } catch (err) {
    notifyError('加载作品数据失败')
    router.replace('/create')
  }
}

function addCharacter() {
  if (form.characters.length >= 10) return
  form.characters.push({ name: '', occupation: '', age: '', gender: '', appearance: '', personality: '', speechTone: '', background: '' })
}

function removeCharacter(index) {
  form.characters.splice(index, 1)
}

function addOpening() {
  if (form.openings.length >= 10) return
  form.openings.push({ label: '', text: '' })
}

function removeOpening(index) {
  if (form.openings.length <= 1) return
  form.openings.splice(index, 1)
}

const sections = [
  { key: 'basic', label: '基础信息' },
  { key: 'characters', label: `角色设定 (${form.characters.length}/10)` },
  { key: 'protagonist', label: '主人公设定' },
  { key: 'world', label: '世界观' },
  { key: 'rules', label: '游玩规则' },
  { key: 'cover', label: '封面' },
]

function switchMode(mode) {
  createMode.value = mode
  activeSection.value = 'basic'
}

function addTag() {
  const text = tagInput.value.trim()
  if (!text || characterForm.tags.length >= 5) return
  if (characterForm.tags.includes(text)) return
  characterForm.tags.push(text)
  tagInput.value = ''
}

function removeTag(index) {
  characterForm.tags.splice(index, 1)
}

function handleTagKeydown(e) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault()
    addTag()
  }
}

async function uploadCharacterAvatar(file) {
  characterUploading.value = true
  try {
    const res = await characterApi.uploadAvatar(file)
    characterForm.avatar = res.data.url
  } catch (err) {
    notifyError('头像上传失败')
  } finally {
    characterUploading.value = false
  }
}

function handleCharacterFileChange(e) {
  const file = e.target.files?.[0]
  if (file) uploadCharacterAvatar(file)
}

function handleCharacterDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadCharacterAvatar(file)
}

async function handleSaveCharacter() {
  if (!characterForm.name.trim() || !characterForm.desc.trim() || !characterForm.personaContent.trim()) return
  characterSaving.value = true
  try {
    const authStore = useAuthStore()
    const res = await characterApi.create({
      name: characterForm.name.trim(),
      desc: characterForm.desc.trim(),
      avatar: characterForm.avatar.trim(),
      author: authStore.userInfo?.nickname || '',
      language: 'zh-Hans',
      tags: characterForm.tags,
      personaContent: characterForm.personaContent.trim(),
      isPublic: 1,
    })
    router.push(`/chat/character/${res.data.id}`)
  } catch (err) {
    notifyError(err.message || '保存失败')
  } finally {
    characterSaving.value = false
  }
}

async function handleSave() {
  if (!form.name.trim() || !form.desc.trim()) return
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      desc: form.desc.trim(),
      detailedIntro: form.detailedIntro.trim(),
      icon: form.icon.trim(),
      characters: form.characters.filter(c => c.name.trim()),
      protagonist: form.protagonist,
      worldSetting: form.worldSetting,
      gameRules: form.gameRules.trim(),
      statusBar: form.statusBar.trim(),
      openingStatements: form.openings.filter(o => o.text.trim()),
      writingStyle: form.writingStyle,
      models: ['deepseek-v4-flash'],
      aiProvider: form.aiProvider || 'deepseek',
    }
    if (isEdit.value && editingWorkId.value) {
      await chatApi.updateWork(editingWorkId.value, payload)
      notifySuccess('作品修改成功')
      router.push(`/chat/${editingWorkId.value}`)
    } else {
      const res = await chatApi.createWork(payload)
      router.push(`/chat/${res.data.id}`)
    }
  } catch (err) {
    notifyError(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function uploadFile(file) {
  uploading.value = true
  try {
    const res = await chatApi.uploadCover(file)
    form.icon = res.data.url
  } catch (err) {
    notifyError('封面上传失败')
  } finally {
    uploading.value = false
  }
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) uploadFile(file)
}

function handleDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadFile(file)
}

const statusTemplate = `【角色状态栏】
伴侣状态：（当前伴侣/关系状态）
好感度：50
欲望值：20`

function useStatusTemplate() {
  form.statusBar = statusTemplate
}

onMounted(() => {
  const mode = route.query.mode
  const editId = route.query.edit

  if (mode) {
    createMode.value = mode === 'character' ? 'character' : 'work'
  }

  if (editId) {
    const id = parseInt(editId, 10)
    if (!isNaN(id) && id > 0) {
      isEdit.value = true
      editingWorkId.value = id
      createMode.value = 'work'
      fetchWorkForEdit(id)
    }
  }
})

const charFields = [
  { key: 'name', label: '姓名 *', placeholder: '角色姓名' },
  { key: 'occupation', label: '职业 *', placeholder: '角色职业' },
  { key: 'age', label: '年龄 *', placeholder: '角色年龄' },
  { key: 'gender', label: '性别 *', placeholder: '男/女/其他' },
  { key: 'appearance', label: '外貌描述 *', placeholder: '身高、发色、体型、穿着等', type: 'textarea' },
  { key: 'personality', label: '角色性格 *', placeholder: '性格、爱好、性癖等', type: 'textarea' },
  { key: 'speechTone', label: '角色语气 *', placeholder: '语气、口吻、说话方式等', type: 'textarea' },
  { key: 'background', label: '背景设定 *', placeholder: '与主角关系、家境、情感经历、出身等', type: 'textarea' },
]
</script>

<template>
  <AppLayout>
    <div class="create-page animate-fade-in">
      <div class="create-header">
        <h1 v-if="isEdit">编辑作品卡</h1>
        <h1 v-else>{{ createMode === 'work' ? '创建作品卡' : '创建角色卡' }}</h1>
        <p v-if="isEdit">修改作品信息，保存后立即生效</p>
        <p v-else>{{ createMode === 'work' ? '填写以下信息，构建你的 AI 互动故事世界' : '创建 AI 角色，用于 1v1 角色对话' }}</p>
      </div>

      <div v-if="!isEdit" class="mode-tabs">
        <button :class="{ active: createMode === 'work' }" @click="switchMode('work')">创建作品卡</button>
        <button :class="{ active: createMode === 'character' }" @click="switchMode('character')">创建角色卡</button>
      </div>

      <div v-if="createMode === 'work'" class="section-nav">
        <button
          v-for="sec in sections"
          :key="sec.key"
          :class="{ active: activeSection === sec.key }"
          @click="activeSection = sec.key"
        >{{ sec.key === 'characters' ? `角色设定 (${form.characters.length}/10)` : sec.label }}</button>
      </div>

      <div v-if="createMode === 'work'" class="form-body">
        <!-- 基础信息 -->
        <section v-show="activeSection === 'basic'" class="form-section">
          <div class="field">
            <label>名称 <span class="required">*</span></label>
            <BaseInput v-model="form.name" placeholder="给你的作品起个名字" />
          </div>
          <div class="field">
            <label>简介 <span class="required">*</span></label>
            <textarea v-model="form.desc" class="field-textarea" rows="3" placeholder="向玩家介绍你的作品，该部分不会展示给 AI" />
          </div>
          <div class="field">
            <label>详细介绍</label>
            <textarea v-model="form.detailedIntro" class="field-textarea" rows="5" placeholder="向玩家详细介绍你的作品——角色、故事背景、世界观、版本信息等" />
          </div>
          <div class="field">
            <label>开场白 ({{ form.openings.length }}/10)</label>
            <div v-for="(item, idx) in form.openings" :key="idx" class="opening-editor-item">
              <div class="opening-item-header">
                <span class="opening-item-num">#{{ idx + 1 }}</span>
                <button v-if="form.openings.length > 1" class="btn-remove-sm" @click="removeOpening(idx)">×</button>
              </div>
              <BaseInput v-model="item.label" placeholder="开场白标题（如：标准开局、激烈开局）" />
              <textarea v-model="item.text" class="field-textarea" rows="3" placeholder="开场白内容..." />
            </div>
            <button class="btn-add-opening" @click="addOpening">+ 添加开场白</button>
          </div>
        </section>

        <!-- 角色设定 -->
        <section v-show="activeSection === 'characters'" class="form-section">
          <div class="section-head">
            <p class="section-desc">添加 0-10 个角色，每个角色包含完整的设定信息</p>
            <BaseButton v-if="form.characters.length < 10" variant="secondary" @click="addCharacter">+ 添加角色</BaseButton>
          </div>

          <div v-if="form.characters.length === 0" class="empty-hint">暂未添加角色，点击上方按钮添加</div>

          <div v-for="(char, ci) in form.characters" :key="ci" class="char-card">
            <div class="char-head">
              <h3>角色 {{ ci + 1 }}</h3>
              <button class="btn-remove" @click="removeCharacter(ci)">删除</button>
            </div>
            <div class="char-fields">
              <div v-for="f in charFields" :key="f.key" class="field">
                <label>{{ f.label }}</label>
                <textarea
                  v-if="f.type === 'textarea'"
                  v-model="char[f.key]"
                  class="field-textarea"
                  rows="2"
                  :placeholder="f.placeholder"
                />
                <BaseInput v-else v-model="char[f.key]" :placeholder="f.placeholder" />
              </div>
            </div>
          </div>
        </section>

        <!-- 主人公设定 -->
        <section v-show="activeSection === 'protagonist'" class="form-section">
          <div class="field">
            <label>主人公名称 <span class="required">*</span></label>
            <BaseInput v-model="form.protagonist.name" placeholder="玩家（您）扮演的角色" />
          </div>
          <div class="field">
            <label>主人公设定 <span class="required">*</span></label>
            <textarea v-model="form.protagonist.description" class="field-textarea" rows="3" placeholder="例：年轻的流浪剑士，身手敏捷，剑法精湛，但过去充满谜团。" />
          </div>
          <div class="field">
            <label>核心动机/目标 <span class="required">*</span></label>
            <textarea v-model="form.protagonist.motivation" class="field-textarea" rows="2" placeholder="例：寻找遗失的记忆和自身的真相，同时在这个充满危险的世界中寻求生存。" />
          </div>
        </section>

        <!-- 世界观 -->
        <section v-show="activeSection === 'world'" class="form-section">
          <div class="field">
            <label>世界名称</label>
            <BaseInput v-model="form.worldSetting.worldName" placeholder="故事开展的世界/国家名" />
          </div>
          <div class="field">
            <label>时代背景与科技/魔法水平</label>
            <textarea v-model="form.worldSetting.eraTech" class="field-textarea" rows="3" placeholder="例：这是一个中世纪背景的奇幻世界，科技水平低下，但魔法力量昌盛。古老的符文魔法与元素魔法并存。" />
          </div>
          <div class="field">
            <label>核心冲突/主题</label>
            <textarea v-model="form.worldSetting.coreConflict" class="field-textarea" rows="2" placeholder="例：黑暗势力入侵与古老预言的实现。人类王国、精灵族之间的联盟与猜忌。" />
          </div>
          <div class="field">
            <label>整体基调与氛围</label>
            <textarea v-model="form.worldSetting.toneAtmosphere" class="field-textarea" rows="2" placeholder="例：史诗般宏大，带有一定的黑暗奇幻色彩和英雄主义精神。" />
          </div>
          <div class="field">
            <label>主线情节设定</label>
            <textarea v-model="form.worldSetting.mainPlot" class="field-textarea" rows="3" placeholder="例：玩家在一次佣兵任务中意外发现了与黑暗势力相关的古老遗物，从而被卷入了一场史诗战争。" />
          </div>
          <div class="field">
            <label>初始剧情状态</label>
            <textarea v-model="form.worldSetting.initialState" class="field-textarea" rows="3" placeholder="例：玩家刚完成一个简单的护送任务，正在前往月光酒馆休息，寻找下一个委托。" />
          </div>
        </section>

        <!-- 游玩规则 -->
        <section v-show="activeSection === 'rules'" class="form-section">
          <div class="field">
            <label>游玩规则</label>
            <textarea v-model="form.gameRules" class="field-textarea" rows="4" placeholder="AI 扮演角色需要遵守的法则" />
          </div>
          <div class="field">
            <label>
              状态栏
              <button class="btn-template" @click="useStatusTemplate">使用模版</button>
            </label>
            <textarea v-model="form.statusBar" class="field-textarea" rows="6" placeholder="可直接使用状态栏模版，也可进行个性化编辑" />
          </div>
        </section>

        <!-- 封面 -->
        <section v-show="activeSection === 'cover'" class="form-section">
          <div class="field">
            <label>封面上传</label>
            <div class="upload-area" @click="$refs.fileInput.click()" @dragover.prevent @drop.prevent="handleDrop">
              <input ref="fileInput" type="file" accept="image/*" class="file-input-hidden" @change="handleFileChange" />
              <div v-if="!form.icon && !uploading" class="upload-placeholder">
                <span class="upload-icon">+</span>
                <span>点击或拖拽上传封面图片</span>
              </div>
              <div v-else-if="uploading" class="upload-placeholder">
                <span>上传中...</span>
              </div>
              <div v-else class="cover-preview-mini">
                <img :src="form.icon" alt="封面预览" />
                <button class="btn-change-cover" @click.stop="form.icon = ''">更换</button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- 角色卡表单 -->
      <div v-if="createMode === 'character'" class="form-body">
        <section class="form-section">
          <div class="field">
            <label>角色名称 <span class="required">*</span></label>
            <BaseInput v-model="characterForm.name" placeholder="给你的角色起个名字" />
          </div>
          <div class="field">
            <label>简介 <span class="required">*</span></label>
            <textarea v-model="characterForm.desc" class="field-textarea" rows="3" placeholder="简要描述角色，展示给其他玩家" />
          </div>
          <div class="field">
            <label>头像上传</label>
            <div class="upload-area" @click="$refs.charFileInput?.click()" @dragover.prevent @drop.prevent="handleCharacterDrop">
              <input ref="charFileInput" type="file" accept="image/*" class="file-input-hidden" @change="handleCharacterFileChange" />
              <div v-if="!characterForm.avatar && !characterUploading" class="upload-placeholder">
                <span class="upload-icon">+</span>
                <span>点击或拖拽上传头像图片</span>
              </div>
              <div v-else-if="characterUploading" class="upload-placeholder">
                <span>上传中...</span>
              </div>
              <div v-else class="cover-preview-mini">
                <img :src="characterForm.avatar" alt="头像预览" />
                <button class="btn-change-cover" @click.stop="characterForm.avatar = ''">更换</button>
              </div>
            </div>
          </div>
          <div class="field">
            <label>标签 ({{ characterForm.tags.length }}/5)</label>
            <div class="tags-input-wrap">
              <div v-for="(tag, idx) in characterForm.tags" :key="idx" class="tag-chip">
                <span>{{ tag }}</span>
                <button class="tag-chip-x" @click="removeTag(idx)">×</button>
              </div>
              <input
                v-if="characterForm.tags.length < 5"
                v-model="tagInput"
                class="tag-input"
                placeholder="输入标签，回车添加"
                @keydown="handleTagKeydown"
                @blur="addTag"
              />
            </div>
          </div>
          <div class="field">
            <label>核心人设 <span class="required">*</span></label>
            <textarea v-model="characterForm.personaContent" class="field-textarea field-textarea-mono" rows="12" placeholder="用自然语言详细描述角色的人设——性格、外貌、语气、背景、说话方式等，将作为 AI 对话的 system prompt 使用" />
          </div>
        </section>
      </div>

      <div class="form-footer">
        <template v-if="createMode === 'work'">
          <BaseButton :loading="saving" :disabled="!form.name.trim() || !form.desc.trim()" size="lg" @click="handleSave">
            {{ isEdit ? '保存修改' : '保存并发布作品卡' }}
          </BaseButton>
        </template>
        <template v-else>
          <BaseButton :loading="characterSaving" :disabled="!characterForm.name.trim() || !characterForm.desc.trim() || !characterForm.personaContent.trim()" size="lg" @click="handleSaveCharacter">
            保存并发布角色卡
          </BaseButton>
        </template>
      </div>
    </div>

    <!-- Writing Style Drawer (work mode only) -->
    <WritingStyleDrawer v-if="createMode === 'work'" v-model="form.writingStyle" />
  </AppLayout>
</template>

<style scoped>
.create-page {
  max-width: 800px;
  margin: 0 auto;
}

.create-header {
  text-align: center;
  margin-bottom: var(--space-lg);
}

.create-header h1 {
  font-size: var(--text-2xl);
  margin-bottom: var(--space-xs);
}

.create-header p {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin: 0;
}

/* section nav */
.mode-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: var(--space-xl);
  justify-content: center;
}

.mode-tabs button {
  padding: 10px 24px;
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text-tertiary);
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  transition: all var(--transition-fast);
}

.mode-tabs button:hover {
  color: var(--text-secondary);
  background: var(--bg-card);
}

.mode-tabs button.active {
  color: var(--color-misty-blue-soft);
  background: rgba(123, 156, 191, 0.1);
  border-color: rgba(123, 156, 191, 0.2);
}

.section-nav {
  display: flex;
  gap: 4px;
  margin-bottom: var(--space-xl);
  flex-wrap: wrap;
}

.section-nav button {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  transition: all var(--transition-fast);
}

.section-nav button:hover {
  color: var(--text-secondary);
  background: var(--bg-card);
}

.section-nav button.active {
  color: var(--color-misty-blue-soft);
  background: rgba(123, 156, 191, 0.1);
  border-color: rgba(123, 156, 191, 0.2);
}

/* form body */
.form-body {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
  margin-bottom: var(--space-xl);
  min-height: 300px;
}

.form-section {
  animation: fadeIn 0.2s ease-out;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.section-desc {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  margin: 0;
}

.empty-hint {
  text-align: center;
  color: var(--text-tertiary);
  padding: var(--space-3xl);
  font-size: var(--text-sm);
}

.field {
  margin-bottom: var(--space-lg);
}

.field label {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.required {
  color: var(--color-crimson-soft);
}

.field-textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: var(--font-sans);
  line-height: var(--leading-relaxed);
  resize: vertical;
  transition: border-color var(--transition-fast);
}

.field-textarea:focus {
  outline: none;
  border-color: var(--border-focus);
}

.field-textarea::placeholder {
  color: var(--text-tertiary);
}

/* character card */
.char-card {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-card);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.char-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.char-head h3 {
  font-size: var(--text-base);
  margin: 0;
}

.btn-remove {
  font-size: var(--text-xs);
  color: var(--color-crimson-soft);
  cursor: pointer;
}

.btn-template {
  font-size: var(--text-xs);
  color: var(--color-misty-blue-soft);
  cursor: pointer;
  border: 1px solid rgba(123, 156, 191, 0.2);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  background: transparent;
}

.btn-template:hover {
  background: rgba(123, 156, 191, 0.1);
}

/* cover preview */
.upload-area {
  border: 2px dashed var(--border-input);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color var(--transition-fast);
  overflow: hidden;
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-area:hover {
  border-color: var(--color-misty-blue-soft);
}

.file-input-hidden {
  display: none;
}

.upload-placeholder {
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.upload-icon {
  display: block;
  font-size: 32px;
  margin-bottom: var(--space-sm);
  color: var(--text-tertiary);
}

.cover-preview-mini {
  position: relative;
  width: 100%;
}

.cover-preview-mini img {
  width: 100%;
  max-height: 320px;
  object-fit: cover;
  display: block;
}

.btn-change-cover {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: var(--text-xs);
  cursor: pointer;
}

/* opening editor */
.opening-editor-item {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
}

.opening-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.opening-item-num {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: 600;
}

.btn-remove-sm {
  font-size: 14px;
  background: none;
  border: none;
  color: var(--color-crimson-soft);
  cursor: pointer;
  padding: 2px 6px;
  line-height: 1;
}

.btn-add-opening {
  display: block;
  width: 100%;
  padding: 10px;
  border: 1px dashed var(--border-primary);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-add-opening:hover {
  border-color: var(--color-misty-blue-soft);
  color: var(--color-misty-blue-soft);
}

.field-textarea-mono {
  font-family: var(--font-mono, 'Consolas', 'Monaco', monospace);
  font-size: 13px;
}

/* tags */
.tags-input-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  padding: 8px 10px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  min-height: 42px;
  transition: border-color var(--transition-fast);
}

.tags-input-wrap:focus-within {
  border-color: var(--border-focus);
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(123, 156, 191, 0.12);
  border: 1px solid rgba(123, 156, 191, 0.2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--color-misty-blue-soft);
}

.tag-chip-x {
  font-size: 12px;
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
  opacity: 0.7;
}

.tag-chip-x:hover {
  opacity: 1;
}

.tag-input {
  flex: 1;
  min-width: 100px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  padding: 2px 0;
}

.tag-input::placeholder {
  color: var(--text-tertiary);
}

/* footer */
.form-footer {
  text-align: center;
  padding-bottom: var(--space-3xl);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
