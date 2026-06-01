<template>
  <AppLayout>
    <div class="page">
      <div class="page-header">
        <div>
          <h1>{{ t('work.my_works') }}</h1>
          <span class="total-hint">{{ t('work.total_count', { n: totalCount }) }}</span>
        </div>
        <button class="btn-primary" @click="goCreate">
          {{ t('work.create_new') }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="skeleton-grid">
        <div v-for="n in 8" :key="n" class="skeleton-card" />
      </div>

      <!-- Empty -->
      <div v-else-if="!workList.length" class="empty-state">
        <div class="empty-icon">◇</div>
        <p>{{ t('work.empty_hint') }}</p>
        <button class="btn-primary" @click="goCreate">
          {{ t('work.go_create') }}
        </button>
      </div>

      <!-- Data Grid -->
      <div v-else class="work-grid">
        <div
          v-for="work in workList"
          :key="work.id"
          class="work-card"
          @click="openChat(work)"
        >
          <div class="card-image">
            <img v-if="work.cover" :src="work.cover" :alt="work.name" />
            <div v-else class="placeholder">{{ work.name.slice(0, 2) }}</div>
            <div class="card-overlay">
              <button class="btn-chat" @click.stop="openChat(work)">
                {{ t('common.start_chat') }}
              </button>
              <button class="btn-edit" @click.stop="editWork(work)">
                {{ t('common.edit') }}
              </button>
              <button class="btn-delete" @click.stop="deleteWork(work.id)">
                {{ t('common.delete') }}
              </button>
            </div>
          </div>
          <div class="card-content">
            <h3>{{ work.name }}</h3>
            <p class="desc" v-if="work.desc">{{ work.desc }}</p>
            <p class="author" v-if="work.author">— {{ work.author }}</p>
            <div class="card-stats">
              <span>💬 {{ work.useCount || 0 }}</span>
              <span class="card-time">{{ formatTime(work.createTime) }}</span>
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
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { chatApi } from '../api/chat';
import AppLayout from '../layouts/AppLayout.vue';
import { notifySuccess, notifyError } from '../utils/notify';
import BasePagination from '../components/base/BasePagination.vue';

const { t } = useI18n();
const router = useRouter();

const workList = ref([]);
const totalCount = ref(0);
const loading = ref(false);

const pagination = ref({ pageNum: 1, pageSize: 12 });

const fetchList = async () => {
  loading.value = true;
  try {
    const res = await chatApi.getMyWorks({
      pageNum: pagination.value.pageNum,
      pageSize: pagination.value.pageSize,
    });
    workList.value = res.data.list;
    totalCount.value = res.data.total;
  } catch (err) {
    notifyError(err.message || t('common.error'));
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page) => {
  pagination.value.pageNum = page;
  fetchList();
};

const goCreate = () => {
  router.push('/create?mode=work');
};

const openChat = (work) => {
  router.push(`/chat/${work.id}`);
};

const editWork = (work) => {
  router.push(`/create?mode=work&edit=${work.id}`);
};

const deleteWork = async (id) => {
  if (!confirm(t('work.delete_confirm'))) return;

  try {
    await chatApi.deleteWork(id);
    notifySuccess(t('work.delete_success'));
    fetchList();
  } catch (err) {
    notifyError(err.message || t('common.error'));
  }
};

const formatTime = (timeStr) => {
  if (!timeStr) return '';
  const d = new Date(timeStr);
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${month}-${day}`;
};



onMounted(() => {
  fetchList();
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

.work-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-lg);
}

.work-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-base);
}

.work-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-primary);
}

.card-image {
  position: relative;
  aspect-ratio: 3/4;
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

.work-card:hover .card-overlay {
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
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.card-time {
  color: var(--text-tertiary);
}

/* Skeleton */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-lg);
}

.skeleton-card {
  aspect-ratio: 3/4;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .4; }
}

/* Empty */
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

/* Buttons */
.btn-primary,
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
