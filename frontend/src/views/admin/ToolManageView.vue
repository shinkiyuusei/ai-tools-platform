<script setup>
import { onMounted, reactive, ref } from 'vue'

import { createTool, deleteTool, getToolListAdmin, updateTool } from '../../api/admin'
import BaseButton from '../../components/base/BaseButton.vue'
import BaseInput from '../../components/base/BaseInput.vue'
import BasePagination from '../../components/base/BasePagination.vue'
import AppLayout from '../../layouts/AppLayout.vue'
import { formatTokens } from '../../utils/format'

const listData = ref({ list: [], total: 0, pageNum: 1, pageSize: 10 })
const dialogVisible = ref(false)
const loading = ref(false)
const isEdit = ref(false)

const drawerVisible = ref(false)
const activeItem = ref(null)
const expandedSections = reactive({})

const form = reactive({
  id: null, name: '', icon: '', desc: '', useDesc: '',
  formConfig: '', aiApi: 'deepseek', isFree: 1, isVip: 0, sortOrder: 0, status: 1,
})

const fetchList = async () => {
  loading.value = true
  try {
    const res = await getToolListAdmin({ pageNum: listData.value.pageNum, pageSize: listData.value.pageSize })
    listData.value.list = res.data.list
    listData.value.total = res.data.total
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null, name: '', icon: '', desc: '', useDesc: '',
    formConfig: '', aiApi: 'deepseek', isFree: 1, isVip: 0, sortOrder: 0, status: 1,
  })
  dialogVisible.value = true
}

const openEdit = (item) => {
  isEdit.value = true
  Object.assign(form, {
    id: item.id, name: item.name, icon: item.icon || '', desc: item.desc || '',
    useDesc: item.useDesc || '',
    formConfig: typeof item.formConfig === 'string' ? item.formConfig : JSON.stringify(item.formConfig || {}, null, 2),
    aiApi: item.aiApi || 'deepseek', isFree: item.isFree ?? 1, isVip: item.isVip ?? 0,
    sortOrder: item.sortOrder ?? 0, status: item.status ?? 1,
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name) return
  loading.value = true
  try {
    let fc = form.formConfig
    if (typeof fc === 'string' && fc.trim()) {
      try { fc = JSON.parse(fc) } catch { fc = [] }
    } else if (!fc) { fc = [] }
    const data = { ...form, formConfig: fc }
    if (isEdit.value) {
      await updateTool(form.id, data)
    } else {
      await createTool(data)
    }
    dialogVisible.value = false
    fetchList()
  } catch (err) {
    window.dispatchEvent(new CustomEvent('app:error', { detail: err.message || '操作失败' }))
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id) => {
  if (!confirm('确定删除此工具？')) return
  await deleteTool(id)
  if (activeItem.value?.id === id) {
    drawerVisible.value = false
    activeItem.value = null
  }
  fetchList()
}

const handlePageChange = (page) => {
  listData.value.pageNum = page
  fetchList()
}

const openDrawer = (item) => {
  activeItem.value = item
  drawerVisible.value = true
  Object.keys(expandedSections).forEach((k) => delete expandedSections[k])
}

const closeDrawer = () => {
  drawerVisible.value = false
  activeItem.value = null
}

const toggleSection = (key) => {
  expandedSections[key] = !expandedSections[key]
}

const fmtScore = (v) => {
  const n = Number(v || 0)
  return n > 0 ? n.toFixed(1) : '-'
}

const statusLabel = (s) => s === 1 ? '上架' : '下架'

onMounted(fetchList)
</script>

<template>
  <AppLayout>
    <div class="page">
      <div class="header-row">
        <h1>作品管理</h1>
        <BaseButton @click="openCreate">新增作品</BaseButton>
      </div>

      <div v-if="listData.list.length" class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th><th>图标</th><th>名称</th><th>AI接口</th><th>Token消耗</th><th>评分</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in listData.list" :key="item.id"
              :class="{ 'row-active': activeItem?.id === item.id }"
              @click="openDrawer(item)">
              <td>{{ item.id }}</td>
              <td><img v-if="item.icon" :src="item.icon" class="icon-preview" /></td>
              <td class="name-cell">{{ item.name }}</td>
              <td>{{ item.aiApi || '-' }}</td>
              <td>{{ formatTokens(item.useCount) }}</td>
              <td>{{ fmtScore(item.rating) }}</td>
              <td><span :class="['status-tag', item.status === 1 ? 'on' : 'off']">{{ statusLabel(item.status) }}</span></td>
              <td class="actions-cell" @click.stop>
                <button class="action-btn" @click="openEdit(item)">编辑</button>
                <button class="action-btn danger" @click="handleDelete(item.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty">暂无作品数据</div>

      <BasePagination
        v-if="listData.total > 0"
        :page-num="listData.pageNum"
        :page-size="listData.pageSize"
        :total="listData.total"
        @update:page-num="handlePageChange"
      />

      <!-- Edit Dialog -->
      <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
        <div class="dialog dialog-wide">
          <h2>{{ isEdit ? '编辑作品' : '新增作品' }}</h2>
          <div class="dialog-body">
            <div class="form-row">
              <div class="form-group flex-2">
                <BaseInput v-model="form.name" placeholder="作品名称" label="名称 *" />
              </div>
              <div class="form-group flex-1">
                <BaseInput v-model="form.icon" placeholder="图标URL" label="图标" />
              </div>
            </div>
            <div class="form-group">
              <label>描述</label>
              <textarea v-model="form.desc" class="base-textarea" rows="2" placeholder="简短描述" />
            </div>
            <div class="form-group">
              <label>使用说明</label>
              <textarea v-model="form.useDesc" class="base-textarea" rows="3" placeholder="详细使用说明" />
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>AI 接口</label>
                <select v-model="form.aiApi" class="base-select">
                  <option value="deepseek">DeepSeek</option>
                  <option value="openai">OpenAI</option>
                  <option value="claude">Claude</option>
                  <option value="qwen">通义千问</option>
                  <option value="glm">智谱GLM</option>
                  <option value="moonshot">Moonshot</option>
                  <option value="">无</option>
                </select>
              </div>
              <div class="form-group half">
                <BaseInput v-model.number="form.sortOrder" label="排序" placeholder="越小越靠前" />
              </div>
            </div>
            <div class="form-group">
              <label>表单配置 (JSON)</label>
              <textarea v-model="form.formConfig" class="base-textarea mono" rows="8" placeholder='[{"field":"topic","label":"主题","type":"text","required":true}]' />
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>状态</label>
                <select v-model.number="form.status" class="base-select">
                  <option :value="1">上架</option>
                  <option :value="0">下架</option>
                </select>
              </div>
              <div class="form-group half">
                <label>免费工具</label>
                <select v-model.number="form.isFree" class="base-select">
                  <option :value="1">是</option>
                  <option :value="0">否</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>会员专属</label>
                <select v-model.number="form.isVip" class="base-select">
                  <option :value="1">是</option>
                  <option :value="0">否</option>
                </select>
              </div>
            </div>
          </div>
          <div class="dialog-actions">
            <BaseButton variant="secondary" @click="dialogVisible = false">取消</BaseButton>
            <BaseButton :loading="loading" @click="handleSubmit">保存</BaseButton>
          </div>
        </div>
      </div>

      <!-- Detail Drawer -->
      <Teleport to="body">
        <div v-if="drawerVisible" class="drawer-overlay" @click.self="closeDrawer">
          <div class="drawer">
            <template v-if="activeItem">
              <div class="drawer-header">
                <div class="drawer-title-row">
                  <img v-if="activeItem.icon" :src="activeItem.icon" class="drawer-icon" />
                  <span class="drawer-name">{{ activeItem.name }}</span>
                </div>
                <button class="drawer-close" @click="closeDrawer">✕</button>
              </div>

              <div class="drawer-body">
                <!-- Basic Info -->
                <section class="drawer-section">
                  <h3 class="section-title">基础信息</h3>
                  <dl class="info-grid">
                    <template v-if="activeItem.desc">
                      <dt>描述</dt><dd>{{ activeItem.desc }}</dd>
                    </template>
                    <template v-if="activeItem.useDesc">
                      <dt>使用说明</dt><dd>{{ activeItem.useDesc }}</dd>
                    </template>
                    <template v-if="activeItem.author">
                      <dt>作者</dt><dd>{{ activeItem.author }}</dd>
                    </template>
                    <template v-if="activeItem.version">
                      <dt>版本</dt><dd>{{ activeItem.version }}</dd>
                    </template>
                    <template v-if="activeItem.sourceId">
                      <dt>源ID</dt><dd class="source-id">{{ activeItem.sourceId }}</dd>
                    </template>
                    <template v-if="activeItem.detailedIntro">
                      <dt>详细介绍</dt><dd class="pre-wrap">{{ activeItem.detailedIntro }}</dd>
                    </template>
                    <dt>创建时间</dt><dd>{{ activeItem.createTime }}</dd>
                    <dt>更新时间</dt><dd>{{ activeItem.updateTime || '-' }}</dd>
                  </dl>
                </section>

                <!-- Operation Config -->
                <section class="drawer-section">
                  <h3 class="section-title">运营配置</h3>
                  <dl class="info-grid">
                    <dt>免费</dt><dd>{{ activeItem.isFree ? '是' : '否' }}</dd>
                    <dt>VIP专属</dt><dd>{{ activeItem.isVip ? '是' : '否' }}</dd>
                    <dt>排序</dt><dd>{{ activeItem.sortOrder }}</dd>
                    <dt>状态</dt><dd><span :class="['status-tag', activeItem.status === 1 ? 'on' : 'off']">{{ statusLabel(activeItem.status) }}</span></dd>
                    <dt>AI接口</dt><dd>{{ activeItem.aiApi || '-' }}</dd>
                    <dt>标签</dt><dd>{{ activeItem.tagIds || '-' }}</dd>
                    <template v-if="activeItem.models?.length">
                      <dt>可用模型</dt><dd>{{ activeItem.models.join(', ') }}</dd>
                    </template>
                    <template v-if="activeItem.modelConfig">
                      <dt>模型配置</dt><dd class="pre-wrap">{{ JSON.stringify(activeItem.modelConfig, null, 2) }}</dd>
                    </template>
                  </dl>
                </section>

                <!-- Statistics -->
                <section class="drawer-section">
                  <h3 class="section-title">统计数据</h3>
                  <div class="stats-row">
                    <div class="stat-card">
                      <div class="stat-value">{{ activeItem.useCount?.toLocaleString() }}</div>
                      <div class="stat-label">Token消耗</div>
                    </div>
                    <div class="stat-card">
                      <div class="stat-value">{{ fmtScore(activeItem.rating) }}</div>
                      <div class="stat-label">评分均分</div>
                    </div>
                    <div class="stat-card">
                      <div class="stat-value">{{ activeItem.ratingCount ?? 0 }}</div>
                      <div class="stat-label">评分人数</div>
                    </div>
                    <div class="stat-card">
                      <div class="stat-value">{{ activeItem.convCount ?? 0 }}</div>
                      <div class="stat-label">对话数</div>
                    </div>
                    <div v-if="activeItem.formStats?.players_count !== undefined" class="stat-card">
                      <div class="stat-value">{{ activeItem.formStats.players_count?.toLocaleString() }}</div>
                      <div class="stat-label">游玩人数</div>
                    </div>
                    <div v-if="activeItem.formStats?.favorites_count !== undefined" class="stat-card">
                      <div class="stat-value">{{ activeItem.formStats.favorites_count?.toLocaleString() }}</div>
                      <div class="stat-label">收藏数</div>
                    </div>
                    <div v-if="activeItem.formStats?.like_count !== undefined" class="stat-card">
                      <div class="stat-value">{{ activeItem.formStats.like_count?.toLocaleString() }}</div>
                      <div class="stat-label">点赞数</div>
                    </div>
                  </div>
                </section>

                <!-- Work Content -->
                <section v-if="activeItem.characters?.length || activeItem.protagonist || activeItem.worldSetting" class="drawer-section">
                  <h3 class="section-title">作品内容</h3>

                  <!-- Characters -->
                  <div v-if="activeItem.characters?.length" class="subsection">
                    <button class="collapse-toggle" @click="toggleSection('characters')">
                      <span :class="['collapse-arrow', { open: expandedSections['characters'] }]">▸</span>
                      角色列表 ({{ activeItem.characters.length }})
                    </button>
                    <div v-if="expandedSections['characters']" class="collapse-body">
                      <div v-for="(c, i) in activeItem.characters" :key="i" class="char-card">
                        <div class="char-card-header">{{ c.name || '未命名' }} <span v-if="c.occupation" class="char-occupation">· {{ c.occupation }}</span></div>
                        <dl class="char-grid">
                          <template v-if="c.age"><dt>年龄</dt><dd>{{ c.age }}</dd></template>
                          <template v-if="c.gender"><dt>性别</dt><dd>{{ c.gender }}</dd></template>
                          <template v-if="c.appearance"><dt>外貌</dt><dd>{{ c.appearance }}</dd></template>
                          <template v-if="c.personality"><dt>性格</dt><dd>{{ c.personality }}</dd></template>
                          <template v-if="c.speechTone"><dt>语气</dt><dd>{{ c.speechTone }}</dd></template>
                          <template v-if="c.background"><dt>背景</dt><dd>{{ c.background }}</dd></template>
                        </dl>
                      </div>
                    </div>
                  </div>

                  <!-- Protagonist -->
                  <div v-if="activeItem.protagonist" class="subsection">
                    <button class="collapse-toggle" @click="toggleSection('protagonist')">
                      <span :class="['collapse-arrow', { open: expandedSections['protagonist'] }]">▸</span>
                      主人公：{{ activeItem.protagonist.name || '未命名' }}
                    </button>
                    <div v-if="expandedSections['protagonist']" class="collapse-body">
                      <dl class="info-grid">
                        <template v-if="activeItem.protagonist.description"><dt>设定</dt><dd>{{ activeItem.protagonist.description }}</dd></template>
                        <template v-if="activeItem.protagonist.motivation"><dt>核心动机</dt><dd>{{ activeItem.protagonist.motivation }}</dd></template>
                      </dl>
                    </div>
                  </div>

                  <!-- World Setting -->
                  <div v-if="activeItem.worldSetting" class="subsection">
                    <button class="collapse-toggle" @click="toggleSection('world')">
                      <span :class="['collapse-arrow', { open: expandedSections['world'] }]">▸</span>
                      世界观：{{ activeItem.worldSetting.worldName || '未命名' }}
                    </button>
                    <div v-if="expandedSections['world']" class="collapse-body">
                      <dl class="info-grid">
                        <template v-if="activeItem.worldSetting.eraTech"><dt>时代背景</dt><dd>{{ activeItem.worldSetting.eraTech }}</dd></template>
                        <template v-if="activeItem.worldSetting.coreConflict"><dt>核心冲突</dt><dd>{{ activeItem.worldSetting.coreConflict }}</dd></template>
                        <template v-if="activeItem.worldSetting.toneAtmosphere"><dt>整体基调</dt><dd>{{ activeItem.worldSetting.toneAtmosphere }}</dd></template>
                        <template v-if="activeItem.worldSetting.mainPlot"><dt>主线情节</dt><dd>{{ activeItem.worldSetting.mainPlot }}</dd></template>
                        <template v-if="activeItem.worldSetting.initialState"><dt>初始剧情</dt><dd class="pre-wrap">{{ activeItem.worldSetting.initialState }}</dd></template>
                      </dl>
                    </div>
                  </div>

                  <!-- Game Rules -->
                  <div v-if="activeItem.gameRules" class="subsection">
                    <button class="collapse-toggle" @click="toggleSection('rules')">
                      <span :class="['collapse-arrow', { open: expandedSections['rules'] }]">▸</span>
                      游玩规则
                    </button>
                    <div v-if="expandedSections['rules']" class="collapse-body">
                      <p class="content-text pre-wrap">{{ activeItem.gameRules }}</p>
                    </div>
                  </div>

                  <!-- Status Bar -->
                  <div v-if="activeItem.statusBar" class="subsection">
                    <button class="collapse-toggle" @click="toggleSection('status')">
                      <span :class="['collapse-arrow', { open: expandedSections['status'] }]">▸</span>
                      状态栏
                    </button>
                    <div v-if="expandedSections['status']" class="collapse-body">
                      <p class="content-text pre-wrap">{{ activeItem.statusBar }}</p>
                    </div>
                  </div>

                  <!-- Opening -->
                  <div v-if="activeItem.opening" class="subsection">
                    <button class="collapse-toggle" @click="toggleSection('opening')">
                      <span :class="['collapse-arrow', { open: expandedSections['opening'] }]">▸</span>
                      开场白
                    </button>
                    <div v-if="expandedSections['opening']" class="collapse-body">
                      <p class="content-text pre-wrap">{{ activeItem.opening }}</p>
                    </div>
                  </div>

                  <!-- Writing Style -->
                  <div v-if="activeItem.writingStyle" class="subsection">
                    <button class="collapse-toggle" @click="toggleSection('style')">
                      <span :class="['collapse-arrow', { open: expandedSections['style'] }]">▸</span>
                      写作风格
                    </button>
                    <div v-if="expandedSections['style']" class="collapse-body">
                      <dl class="info-grid">
                        <template v-if="activeItem.writingStyle.sensoryDensity"><dt>感官密度</dt><dd>{{ activeItem.writingStyle.sensoryDensity }}</dd></template>
                        <template v-if="activeItem.writingStyle.pacingPreference"><dt>节奏偏好</dt><dd>{{ activeItem.writingStyle.pacingPreference }}</dd></template>
                        <template v-if="activeItem.writingStyle.powerIntensity"><dt>权力强度</dt><dd>{{ activeItem.writingStyle.powerIntensity }}</dd></template>
                        <template v-if="activeItem.writingStyle.proseStyle"><dt>文风类型</dt><dd>{{ activeItem.writingStyle.proseStyle }}</dd></template>
                        <template v-if="activeItem.writingStyle.wordCount"><dt>目标字数</dt><dd>{{ activeItem.writingStyle.wordCount }}</dd></template>
                      </dl>
                    </div>
                  </div>
                </section>

                <!-- Raw FormConfig -->
                <section v-if="activeItem.formConfig" class="drawer-section">
                  <button class="collapse-toggle" @click="toggleSection('rawConfig')">
                    <span :class="['collapse-arrow', { open: expandedSections['rawConfig'] }]">▸</span>
                    原始 FormConfig JSON
                  </button>
                  <div v-if="expandedSections['rawConfig']" class="collapse-body">
                    <pre class="raw-json">{{ typeof activeItem.formConfig === 'string' ? activeItem.formConfig : JSON.stringify(activeItem.formConfig, null, 2) }}</pre>
                  </div>
                </section>
              </div>
            </template>
          </div>
        </div>
      </Teleport>
    </div>
  </AppLayout>
</template>

<style scoped>
.page {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.header-row h1 {
  font-size: var(--text-lg);
  margin: 0;
}

.table-wrap { overflow-x: auto; }

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th, .table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-card);
  font-size: var(--text-sm);
  white-space: nowrap;
}

.table th {
  color: var(--text-tertiary);
  font-weight: 600;
}

.table tbody tr {
  cursor: pointer;
  transition: background var(--transition-fast);
}

.table tbody tr:hover { background: var(--bg-elevated); }

.table tbody tr.row-active {
  background: rgba(123, 156, 191, 0.08);
  border-left: 3px solid var(--color-misty-blue);
}

.name-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.icon-preview {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  background: var(--bg-tertiary);
}

.status-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.status-tag.on { color: #4caf8e; background: rgba(76, 175, 142, 0.1); }
.status-tag.off { color: #c85554; background: rgba(200, 85, 84, 0.1); }

.actions-cell { display: flex; gap: 6px; }

.action-btn {
  border: none;
  background: none;
  color: var(--color-misty-blue-soft);
  cursor: pointer;
  font-size: var(--text-xs);
}

.action-btn.danger { color: var(--color-crimson-soft); }

.empty {
  text-align: center;
  padding: var(--space-3xl);
  color: var(--text-tertiary);
}

/* Dialog */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  z-index: var(--z-modal);
  padding-top: 40px;
}

.dialog {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  padding: var(--space-xl);
  width: 640px;
  max-width: 92vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.dialog-wide { width: 720px; }

.dialog h2 {
  font-size: var(--text-lg);
  margin: 0 0 var(--space-lg);
  flex-shrink: 0;
}

.dialog-body {
  overflow-y: auto;
  flex: 1;
  padding-right: var(--space-sm);
}

.form-group { margin-bottom: var(--space-md); }

.form-group label {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
  font-weight: 500;
}

.form-row { display: flex; gap: var(--space-md); }
.half { flex: 1; }
.flex-1 { flex: 1; }
.flex-2 { flex: 2; }

.base-textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  resize: vertical;
  line-height: var(--leading-relaxed);
  font-family: inherit;
}

.base-textarea.mono {
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.base-textarea:focus {
  outline: none;
  border-color: var(--border-focus);
}

.base-select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.dialog-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  margin-top: var(--space-lg);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-card);
  flex-shrink: 0;
}

/* Drawer */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: var(--z-modal);
  display: flex;
  justify-content: flex-end;
}

.drawer {
  width: 520px;
  max-width: 92vw;
  height: 100%;
  background: var(--bg-card);
  border-left: 1px solid var(--border-card);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.25s ease;
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--border-card);
  flex-shrink: 0;
}

.drawer-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  min-width: 0;
}

.drawer-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  background: var(--bg-tertiary);
  flex-shrink: 0;
}

.drawer-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-close {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-input);
  background: transparent;
  color: var(--text-tertiary);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.drawer-close:hover { color: var(--text-primary); border-color: var(--text-tertiary); }

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg) var(--space-xl);
}

.drawer-section {
  margin-bottom: var(--space-xl);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 var(--space-md);
  padding-bottom: var(--space-xs);
  border-bottom: 1px solid var(--border-card);
}

.info-grid {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 8px var(--space-sm);
  margin: 0;
}

.info-grid dt {
  font-size: 12px;
  color: var(--text-tertiary);
}

.info-grid dd {
  font-size: 13px;
  color: var(--text-primary);
  margin: 0;
  word-break: break-word;
}

.pre-wrap { white-space: pre-wrap; }

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-sm);
}

.stat-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

/* Collapsible sections */
.subsection {
  margin-top: var(--space-sm);
}

.collapse-toggle {
  width: 100%;
  padding: 10px 0;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: color var(--transition-fast);
}

.collapse-toggle:hover { color: var(--text-primary); }

.collapse-arrow {
  display: inline-block;
  font-size: 10px;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.collapse-arrow.open { transform: rotate(90deg); }

.collapse-body {
  padding: var(--space-sm) 0 var(--space-md) var(--space-md);
}

.char-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
}

.char-card-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.char-occupation {
  font-weight: 400;
  color: var(--text-tertiary);
}

.char-grid {
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: 6px var(--space-sm);
  margin: 0;
}

.char-grid dt {
  font-size: 11px;
  color: var(--text-tertiary);
}

.char-grid dd {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  word-break: break-word;
}

.content-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.model-tag {
  padding: 3px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
}

.raw-json {
  background: var(--bg-input);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  font-size: 11px;
  line-height: 1.6;
  color: var(--text-secondary);
  overflow-x: auto;
  white-space: pre;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
}

@media (max-width: 768px) {
  .form-row { flex-direction: column; gap: 0; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .drawer { width: 100%; max-width: 100%; }
}
</style>
