<template>
  <AppLayout>
    <div class="page">
      <div class="page-header">
        <div>
          <h1>{{ t('character.my_characters') }}</h1>
          <span class="total-hint">{{ t('character.total_count', { n: totalCount }) }}</span>
        </div>
        <button class="btn-primary" @click="openCreate">
          {{ t('character.create_new') }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="skeleton-grid">
        <div v-for="n in 8" :key="n" class="skeleton-card" />
      </div>

      <!-- Empty -->
      <div v-else-if="!characterList.length" class="empty-state">
        <div class="empty-icon">◇</div>
        <p>{{ t('character.empty_hint') }}</p>
        <button class="btn-primary" @click="openCreate">
          {{ t('character.go_create') }}
        </button>
      </div>

      <!-- Data Grid -->
      <div v-else class="character-grid">
        <div
          v-for="char in characterList"
          :key="char.id"
          class="character-card"
          @click="viewCharacter(char)"
        >
          <div class="card-image">
            <img v-if="char.avatar" :src="char.avatar" :alt="char.name" />
            <div v-else class="placeholder">{{ char.name.slice(0, 2) }}</div>
            <div class="card-overlay">
              <button class="btn-chat" @click.stop="openChat(char)">
                {{ t('common.start_chat') }}
              </button>
              <button class="btn-edit" @click.stop="editCharacter(char)">
                {{ t('common.edit') }}
              </button>
              <button class="btn-delete" @click.stop="deleteCharacter(char.id)">
                {{ t('common.delete') }}
              </button>
            </div>
          </div>
          <div class="card-content">
            <h3>{{ char.name }}</h3>
            <p class="desc" v-if="char.desc">{{ char.desc }}</p>
            <p class="author" v-if="char.author">— {{ char.author }}</p>
            <div class="card-stats">
              <span>♥ {{ char.likeCount || 0 }}</span>
              <span>👁 {{ char.viewCount || 0 }}</span>
              <span>★ {{ char.collectCount || 0 }}</span>
              <span>💬 {{ char.useCount || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <BasePagination
        v-if="totalCount > 0"
        :current="pagination.pageNum"
        :total="totalCount"
        :page-size="pagination.pageSize"
        @update:page-num="handlePageChange"
      />
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingCharacter" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h2>{{ editingCharacter ? t('character.edit_title') : t('character.create_title') }}</h2>

        <form @submit.prevent="saveCharacter">
          <div class="form-group">
            <label>{{ t('character.name') }} *</label>
            <input v-model="formData.name" type="text" :placeholder="t('character.name_placeholder')" required />
          </div>

          <div class="form-group">
            <label>{{ t('character.desc') }} *</label>
            <input v-model="formData.desc" type="text" :placeholder="t('character.desc_placeholder')" required maxlength="500" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>{{ t('character.author') }}</label>
              <input v-model="formData.author" type="text" :placeholder="t('character.author_placeholder')" />
            </div>
            <div class="form-group">
              <label>{{ t('character.language') }}</label>
              <select v-model="formData.language">
                <option value="zh-Hans">简体中文</option>
                <option value="en">English</option>
                <option value="ja">日本語</option>
                <option value="ko">한국어</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>{{ t('character.avatar') }}</label>
            <div class="avatar-upload">
              <div v-if="formData.avatar" class="avatar-preview">
                <img :src="formData.avatar" alt="Avatar" />
                <button type="button" class="btn-remove" @click="formData.avatar = ''">×</button>
              </div>
              <div v-else class="avatar-placeholder" @click="triggerFileUpload">
                <span>+</span>
              </div>
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                style="display: none"
                @change="handleFileUpload"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>{{ t('character.category') }}</label>
              <select v-model="formData.category">
                <option value="0">{{ t('common.select') }}</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ t('character.tags') }}</label>
              <input v-model="tagInput" type="text" :placeholder="t('character.tags_placeholder')" @keydown.enter.prevent="addTag" />
              <div class="tag-chips" v-if="formData.tags.length">
                <span v-for="(tag, i) in formData.tags" :key="i" class="tag-chip">
                  {{ tag }}
                  <button type="button" class="tag-remove" @click="removeTag(i)">×</button>
                </span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>{{ t('character.persona_content') }} *</label>
            <textarea
              v-model="formData.personaContent"
              :placeholder="t('character.persona_content_placeholder')"
              rows="15"
              class="persona-editor"
              required
            />
            <span class="hint">{{ t('character.persona_content_hint') }}</span>
          </div>

          <div class="form-group">
            <label>
              <input v-model="formData.isPublic" type="checkbox" />
              {{ t('character.is_public') }}
            </label>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="closeModal">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? t('common.loading') : t('common.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { characterApi } from '../api/character';
import AppLayout from '../layouts/AppLayout.vue';
import { notifySuccess, notifyError } from '../utils/notify';
import BasePagination from '../components/base/BasePagination.vue';

const { t } = useI18n();
const router = useRouter();

const characterList = ref([]);
const totalCount = ref(0);
const loading = ref(false);
const saving = ref(false);
const showCreateModal = ref(false);
const editingCharacter = ref(null);
const fileInput = ref(null);
const tagInput = ref('');

const pagination = ref({ pageNum: 1, pageSize: 12 });

const categories = ref([
  { id: 1, name: '恋爱' },
  { id: 2, name: '角色' },
  { id: 3, name: '剧情' },
  { id: 4, name: '幻想' },
  { id: 5, name: '日常' }
]);

const emptyForm = () => ({
  name: '',
  desc: '',
  avatar: '',
  author: '',
  language: 'zh-Hans',
  category: 0,
  tags: [],
  personaContent: '',
  isPublic: true
});

const formData = ref(emptyForm());

const loadCharacters = async () => {
  loading.value = true;
  try {
    const res = await characterApi.getMyList({
      pageNum: pagination.value.pageNum,
      pageSize: pagination.value.pageSize,
    });
    characterList.value = res.data.list;
    totalCount.value = res.data.total;
  } catch (err) {
    notifyError(err.message || t('common.error'));
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page) => {
  pagination.value.pageNum = page;
  loadCharacters();
};

const openCreate = () => {
  editingCharacter.value = null;
  formData.value = emptyForm();
  showCreateModal.value = true;
};

const viewCharacter = (char) => {
  router.push(`/character/${char.id}`);
};

const openChat = (char) => {
  router.push(`/chat/character/${char.id}`);
};

const editCharacter = (char) => {
  editingCharacter.value = char;
  formData.value = {
    name: char.name || '',
    desc: char.desc || '',
    avatar: char.avatar || '',
    author: char.author || '',
    language: char.language || 'zh-Hans',
    category: char.category || 0,
    tags: Array.isArray(char.tags) ? [...char.tags] : [],
    personaContent: char.personaContent || '',
    isPublic: char.isPublic !== 0
  };
};

const deleteCharacter = async (id) => {
  if (!confirm(t('character.delete_confirm'))) return;

  try {
    await characterApi.delete(id);
    notifySuccess(t('character.delete_success'));
    loadCharacters();
  } catch (err) {
    notifyError(err.message || t('common.error'));
  }
};

const addTag = () => {
  const val = tagInput.value.trim();
  if (val && !formData.value.tags.includes(val)) {
    formData.value.tags.push(val);
  }
  tagInput.value = '';
};

const removeTag = (index) => {
  formData.value.tags.splice(index, 1);
};

const saveCharacter = async () => {
  saving.value = true;
  try {
    const data = {
      name: formData.value.name,
      desc: formData.value.desc,
      avatar: formData.value.avatar,
      author: formData.value.author,
      language: formData.value.language,
      category: formData.value.category,
      tags: formData.value.tags,
      personaContent: formData.value.personaContent,
      isPublic: formData.value.isPublic ? 1 : 0
    };

    if (editingCharacter.value) {
      await characterApi.update(editingCharacter.value.id, data);
      notifySuccess(t('character.update_success'));
    } else {
      await characterApi.create(data);
      notifySuccess(t('character.create_success'));
    }

    closeModal();
    loadCharacters();
  } catch (err) {
    notifyError(err.message || t('common.error'));
  } finally {
    saving.value = false;
  }
};

const closeModal = () => {
  showCreateModal.value = false;
  editingCharacter.value = null;
  formData.value = emptyForm();
  tagInput.value = '';
};

const triggerFileUpload = () => {
  fileInput.value?.click();
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const res = await characterApi.uploadAvatar(file);
    formData.value.avatar = res.data.url;
  } catch (err) {
    notifyError(err.message || t('common.error'));
  }
};



onMounted(() => {
  loadCharacters();
});
</script>

<style scoped>
.page {
  padding: var(--space-lg);
  max-width: var(--max-content-width);
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-xl);
}

.page-header h1 {
  font-size: var(--text-xl);
  margin: 0 0 4px 0;
}

.total-hint {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-lg);
}

.character-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-base);
}

.character-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-primary);
}

.card-image {
  position: relative;
  aspect-ratio: 1/1;
  background: var(--bg-tertiary);
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: var(--text-3xl);
  color: var(--text-tertiary);
}

.card-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-overlay);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.character-card:hover .card-overlay {
  opacity: 1;
}

.card-content {
  padding: var(--space-md);
}

.card-content h3 {
  margin: 0 0 var(--space-xs) 0;
  font-size: var(--text-base);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.desc {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin: 0 0 2px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.author {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  margin: 0 0 var(--space-sm) 0;
}

.card-stats {
  display: flex;
  gap: var(--space-sm);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* Skeleton grid */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-lg);
}

.skeleton-card {
  aspect-ratio: 1/1;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .4; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--space-lg);
  opacity: .5;
}

.empty-state p {
  font-size: var(--text-base);
  margin: 0 0 var(--space-lg) 0;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.modal-content {
  background: var(--bg-elevated);
  padding: var(--space-xl);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-card);
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  color: var(--text-primary);
}

.modal-content h2 {
  margin-top: 0;
}

.form-group {
  margin-bottom: var(--space-lg);
}

.form-row {
  display: flex;
  gap: var(--space-md);
}

.form-row .form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: var(--space-sm);
  font-weight: 500;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  color: var(--text-primary);
  transition: border-color var(--transition-fast);
  box-sizing: border-box;
}

.persona-editor {
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--border-focus);
}

.form-group select {
  color: var(--text-primary);
  background: var(--bg-input);
}

.form-group select option {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.hint {
  display: block;
  margin-top: 4px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.tag-remove {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.avatar-preview {
  position: relative;
  width: 100px;
  height: 100px;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: var(--radius-md);
}

.btn-remove {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-crimson);
  color: white;
  border: none;
  cursor: pointer;
  font-size: var(--text-xs);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-placeholder {
  width: 100px;
  height: 100px;
  border: 2px dashed var(--border-input);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: border-color var(--transition-fast);
}

.avatar-placeholder:hover {
  border-color: var(--text-tertiary);
}

.form-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  margin-top: var(--space-xl);
}

.btn-primary,
.btn-secondary,
.btn-chat,
.btn-edit,
.btn-delete {
  padding: 8px 18px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.btn-primary {
  background: var(--color-misty-blue-deep);
  color: #fff;
}

.btn-primary:hover {
  background: var(--color-misty-blue);
}

.btn-primary:disabled {
  opacity: .6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-input);
}

.btn-secondary:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.btn-chat {
  background: var(--color-dark-green-soft);
  color: #fff;
}

.btn-chat:hover {
  background: var(--color-dark-green);
}

.btn-edit {
  background: var(--color-misty-blue-soft);
  color: #fff;
}

.btn-edit:hover {
  background: var(--color-misty-blue);
}

.btn-delete {
  background: var(--color-crimson-soft);
  color: #fff;
}

.btn-delete:hover {
  background: var(--color-crimson);
}
</style>
