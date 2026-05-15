<script setup>
import { computed } from 'vue'

const props = defineProps({
  code: { type: [Number, String], default: 404 },
})

const titleMap = { 400: '请求错误', 403: '无权限', 404: '页面不存在', 500: '服务器异常' }
const descMap = {
  400: '请求参数有误，请检查后重试',
  403: '你的账号没有访问权限',
  404: '页面不存在或已被移除',
  500: '服务器异常，请稍后重试',
}

const title = computed(() => titleMap[props.code] || '未知错误')
const desc = computed(() => descMap[props.code] || '发生了未知错误')
</script>

<template>
  <div class="error-page">
    <span class="error-code">{{ code }}</span>
    <h1>{{ title }}</h1>
    <p>{{ desc }}</p>
    <router-link class="btn" to="/create">返回首页</router-link>
  </div>
</template>

<style scoped>
.error-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: var(--space-xl);
  background: var(--bg-primary);
}

.error-code {
  font-size: 120px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-crimson));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  opacity: 0.6;
}

h1 {
  margin-top: -10px;
  margin-bottom: var(--space-sm);
  font-size: var(--text-xl);
}

p {
  color: var(--text-tertiary);
  margin-bottom: var(--space-xl);
}

.btn {
  display: inline-block;
  background: linear-gradient(135deg, var(--color-misty-blue-deep), var(--color-misty-blue));
  color: #fff;
  padding: 12px 28px;
  border-radius: var(--radius-md);
  text-decoration: none;
  font-weight: 500;
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
}

.btn:hover {
  box-shadow: var(--shadow-glow-misty);
  transform: translateY(-1px);
}
</style>
