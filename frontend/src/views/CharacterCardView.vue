<template>
  <div class="character-card-view">
    <div class="header">
      <h1>{{ isEdit ? t('character.edit_title') : t('character.create_title') }}</h1>
      <button class="btn-primary" @click="showCreateModal = true">
        {{ t('character.create_new') }}
      </button>
    </div>

    <div class="character-grid">
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
          <p class="description">{{ char.description }}</p>
          <div class="card-stats">
            <span>♥ {{ char.like_count }}</span>
            <span>👁 {{ char.view_count }}</span>
            <span>★ {{ char.collect_count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal || editingCharacter" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h2>{{ editingCharacter ? t('character.edit_title') : t('character.create_title') }}</h2>
        
        <form @submit.prevent="saveCharacter">
          <div class="form-group">
            <label>{{ t('character.name') }}</label>
            <input v-model="formData.name" type="text" :placeholder="t('character.name_placeholder')" required />
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

          <div class="form-group">
            <label>{{ t('character.description') }}</label>
            <textarea
              v-model="formData.description"
              :placeholder="t('character.description_placeholder')"
              rows="3"
              required
            />
          </div>

          <div class="form-group">
            <label>{{ t('character.personality') }}</label>
            <textarea
              v-model="formData.personality"
              :placeholder="t('character.personality_placeholder')"
              rows="3"
            />
          </div>

          <div class="form-group">
            <label>{{ t('character.background') }}</label>
            <textarea
              v-model="formData.background"
              :placeholder="t('character.background_placeholder')"
              rows="3"
            />
          </div>

          <div class="form-group">
            <label>{{ t('character.tags') }}</label>
            <input
              v-model="formData.tags"
              type="text"
              :placeholder="t('character.tags_placeholder')"
            />
          </div>

          <div class="form-group">
            <label>{{ t('character.category') }}</label>
            <select v-model="formData.categoryId">
              <option value="0">{{ t('common.select') }}</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
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
            <button type="submit" class="btn-primary">
              {{ t('common.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { characterApi } from '../api/character';

const { t } = useI18n();

const characterList = ref([]);
const showCreateModal = ref(false);
const editingCharacter = ref(null);
const fileInput = ref(null);
const categories = ref([
  { id: 1, name: '恋爱' },
  { id: 2, name: '角色' },
  { id: 3, name: '剧情' },
  { id: 4, name: '幻想' },
  { id: 5, name: '日常' }
]);

const formData = ref({
  name: '',
  avatar: '',
  description: '',
  personality: '',
  background: '',
  tags: '',
  categoryId: 0,
  isPublic: true
});

const isEdit = computed(() => !!editingCharacter.value);

const loadCharacters = async () => {
  try {
    const res = await characterApi.getMyList({ pageNum: 1, pageSize: 50 });
    characterList.value = res.data.list;
  } catch (error) {
    console.error('Failed to load characters:', error);
  }
};

const viewCharacter = (char) => {
  // Navigate to character detail view
  console.log('View character:', char);
};

const editCharacter = (char) => {
  editingCharacter.value = char;
  formData.value = {
    name: char.name,
    avatar: char.avatar,
    description: char.description,
    personality: char.personality,
    background: char.background,
    tags: char.tags,
    categoryId: char.category_id,
    isPublic: char.is_public === 1
  };
};

const deleteCharacter = async (id) => {
  if (!confirm(t('character.delete_confirm'))) return;
  
  try {
    await characterApi.delete(id);
    loadCharacters();
  } catch (error) {
    console.error('Failed to delete character:', error);
  }
};

const saveCharacter = async () => {
  try {
    const data = {
      ...formData.value,
      categoryId: formData.value.categoryId,
      isPublic: formData.value.isPublic ? 1 : 0
    };
    
    if (editingCharacter.value) {
      await characterApi.update(editingCharacter.value.id, data);
    } else {
      await characterApi.create(data);
    }
    
    closeModal();
    loadCharacters();
  } catch (error) {
    console.error('Failed to save character:', error);
  }
};

const closeModal = () => {
  showCreateModal.value = false;
  editingCharacter.value = null;
  formData.value = {
    name: '',
    avatar: '',
    description: '',
    personality: '',
    background: '',
    tags: '',
    categoryId: 0,
    isPublic: true
  };
};

const triggerFileUpload = () => {
  fileInput.value.click();
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const res = await characterApi.uploadAvatar(file);
    formData.value.avatar = res.data.url;
  } catch (error) {
    console.error('Failed to upload avatar:', error);
    alert(t('common.error'));
  }
};

onMounted(() => {
  loadCharacters();
});
</script>

<style scoped>
.character-card-view {
  padding: var(--space-lg);
  max-width: var(--max-content-width);
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xl);
}

.header h1 {
  font-size: var(--text-xl);
  margin: 0;
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
  align-items: center;
  justify-content: center;
  gap: 10px;
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

.description {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin: 0 0 var(--space-sm) 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-stats {
  display: flex;
  gap: var(--space-sm);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

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
  max-width: 600px;
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

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-input);
}

.btn-secondary:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.btn-edit {
  background: var(--color-dark-green-soft);
  color: #fff;
}

.btn-edit:hover {
  background: var(--color-dark-green);
}

.btn-delete {
  background: var(--color-crimson-soft);
  color: #fff;
}

.btn-delete:hover {
  background: var(--color-crimson);
}
</style>
