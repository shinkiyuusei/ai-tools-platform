<script setup>
import { computed, onMounted, ref } from 'vue'
import { createRechargeOrder, getRechargeProducts } from '../api/recharge'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['close', 'success'])
const auth = useAuthStore()

const products = ref([])
const loading = ref(false)
const selectedId = ref(null)
const payChannel = ref('page')

const selectedProduct = computed(() => products.value.find(p => p.id === selectedId.value))

const fetchProducts = async () => {
  try {
    const res = await getRechargeProducts()
    products.value = res.data
    if (products.value.length > 0) {
      selectedId.value = products.value[0].id
    }
  } catch {}
}

const handlePay = async () => {
  if (!selectedId.value) return
  loading.value = true
  try {
    const res = await createRechargeOrder({
      product_id: selectedId.value,
      pay_channel: payChannel.value,
    })
    // 跳转到支付宝支付页面
    window.location.href = res.data.pay_url
  } catch {
    loading.value = false
  }
}

onMounted(fetchProducts)
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-card animate-fade-in">
      <div class="modal-header">
        <h2>积分充值</h2>
        <button class="modal-close" @click="emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <p class="modal-desc">1 人民币 = 1000 积分，选择档位即时充值</p>

        <div class="product-grid">
          <div
            v-for="p in products"
            :key="p.id"
            class="product-card"
            :class="{ active: selectedId === p.id }"
            @click="selectedId = p.id"
          >
            <div class="product-name">{{ p.name }}</div>
            <div class="product-credits">
              <span class="credits-num">{{ (p.total_credits / 1000).toFixed(0) }}K</span>
              <span class="credits-unit">积分</span>
            </div>
            <div v-if="p.bonus > 0" class="product-bonus">送 {{ (p.bonus / 1000).toFixed(0) }}K</div>
            <div class="product-price">
              <span class="price-symbol">¥</span>{{ p.amount }}
            </div>
          </div>
        </div>

        <div class="pay-channel">
          <span class="channel-label">支付方式：</span>
          <label class="channel-radio">
            <input type="radio" v-model="payChannel" value="page" />
            <span>💻 电脑支付</span>
          </label>
          <label class="channel-radio">
            <input type="radio" v-model="payChannel" value="wap" />
            <span>📱 手机支付</span>
          </label>
        </div>

        <button
          class="pay-btn gradient-hero"
          :disabled="loading || !selectedId"
          @click="handlePay"
        >
          {{ loading ? '跳转中...' : `立即支付 ¥${selectedProduct?.amount || 0}` }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(13, 13, 20, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.modal-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  width: 520px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--border-secondary);
}

.modal-header h2 {
  font-size: var(--text-xl);
  font-weight: 600;
}

.modal-close {
  font-size: 18px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: color var(--transition-fast);
}
.modal-close:hover { color: var(--text-primary); }

.modal-body {
  padding: var(--space-xl);
}

.modal-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-lg);
}

.product-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.product-card {
  background: var(--bg-card);
  border: 2px solid var(--border-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.product-card:hover {
  border-color: var(--color-misty-blue-soft);
}

.product-card.active {
  border-color: var(--color-misty-blue);
  background: rgba(123, 156, 191, 0.08);
}

.product-name {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.credits-num {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
}

.credits-unit {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-left: 4px;
}

.product-bonus {
  font-size: var(--text-xs);
  color: var(--color-candy-pink-soft);
  margin-top: 2px;
}

.product-price {
  margin-top: var(--space-sm);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-misty-blue);
}

.price-symbol {
  font-size: var(--text-sm);
}

.pay-channel {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  font-size: var(--text-sm);
}

.channel-label {
  color: var(--text-secondary);
}

.channel-radio {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: var(--text-primary);
}

.pay-btn {
  width: 100%;
  padding: 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.pay-btn:hover:not(:disabled) {
  opacity: 0.9;
  box-shadow: var(--shadow-glow-misty);
}

.pay-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
