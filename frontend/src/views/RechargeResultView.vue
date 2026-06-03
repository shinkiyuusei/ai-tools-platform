<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRechargeOrder } from '../api/recharge'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const statusText = ref('处理中...')
const order = ref(null)
const loading = ref(true)
let pollTimer = null

const fetchOrder = async (orderId) => {
  try {
    const res = await getRechargeOrder(orderId)
    order.value = res.data
    updateStatus(res.data)
    return res.data
  } catch {
    statusText.value = '订单查询失败'
    loading.value = false
    return null
  }
}

const updateStatus = (data) => {
  loading.value = false
  if (data.status === 1 && data.creditsGranted === 1) {
    statusText.value = '充值成功'
    // 刷新积分显示
    auth.refreshCredits()
  } else if (data.status === 1 && data.creditsGranted === 0) {
    statusText.value = '支付成功，积分发放中...'
  } else if (data.status === 0) {
    statusText.value = '等待支付'
  } else {
    statusText.value = '订单状态异常'
  }
}

const startPolling = (orderId, maxSec = 60) => {
  let elapsed = 0
  pollTimer = setInterval(async () => {
    elapsed += 3
    const data = await fetchOrder(orderId)
    if (!data || data.status !== 0) {
      // 支付完成或查询失败，如果积分还没到账继续轮询
      if (data && data.status === 1 && data.creditsGranted === 1) {
        clearInterval(pollTimer)
      }
    }
    if (elapsed >= maxSec) {
      clearInterval(pollTimer)
      if (statusText.value === '等待支付' || statusText.value === '支付成功，积分发放中...') {
        statusText.value = '请稍后在订单记录中查看'
      }
    }
  }, 3000)
}

onMounted(async () => {
  const orderId = route.query.out_trade_no
  if (!orderId) {
    statusText.value = '缺少订单信息'
    loading.value = false
    return
  }
  await fetchOrder(Number(orderId))
  if (order.value && (order.value.status === 0 || order.value.creditsGranted === 0)) {
    startPolling(Number(orderId))
  }
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="result-page">
    <div class="result-card animate-fade-in">
      <div v-if="loading" class="result-loading">
        <div class="spinner"></div>
        <p>查询支付结果...</p>
      </div>
      <template v-else>
        <div class="result-icon" :class="{ success: order?.creditsGranted === 1 }">
          {{ order?.creditsGranted === 1 ? '✓' : order?.status === 1 ? '⏳' : '⏰' }}
        </div>
        <h1 class="result-title">{{ statusText }}</h1>
        <div v-if="order" class="result-detail">
          <div class="detail-row">
            <span class="detail-label">订单编号</span>
            <span class="detail-value">{{ order.orderNo }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">充值金额</span>
            <span class="detail-value">¥{{ order.amount }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">到账积分</span>
            <span class="detail-value">{{ order.totalCredits?.toLocaleString() }}</span>
          </div>
        </div>
        <div class="result-actions">
          <button class="action-btn gradient-hero" @click="router.push('/explore')">返回首页</button>
          <button class="action-btn action-btn--secondary" @click="router.push('/usercenter')">用户中心</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.result-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: var(--space-xl);
}

.result-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-3xl);
  text-align: center;
  width: 420px;
  max-width: 100%;
}

.result-loading .spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-secondary);
  border-top-color: var(--color-misty-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--space-md);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.result-loading p {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.result-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin: 0 auto var(--space-lg);
  background: rgba(238, 162, 180, 0.15);
  color: var(--color-candy-pink-soft);
}

.result-icon.success {
  background: rgba(61, 107, 86, 0.2);
  color: var(--color-dark-green);
}

.result-title {
  font-size: var(--text-xl);
  font-weight: 600;
  margin-bottom: var(--space-xl);
}

.result-detail {
  text-align: left;
  margin-bottom: var(--space-xl);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--border-secondary);
}

.detail-label {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.detail-value {
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: 500;
}

.result-actions {
  display: flex;
  gap: var(--space-md);
}

.action-btn {
  flex: 1;
  padding: 12px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  opacity: 0.9;
}

.action-btn--secondary {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  color: var(--text-secondary);
}

.action-btn--secondary:hover {
  background: var(--bg-secondary);
}
</style>
