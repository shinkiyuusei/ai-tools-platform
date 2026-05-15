import { defineStore } from 'pinia'
import { ref } from 'vue'

const TOKEN_KEY = 'token'
const REFRESH_TOKEN_KEY = 'refreshToken'

function loadUser() {
  try {
    const raw = localStorage.getItem('userInfo')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const refreshToken = ref(localStorage.getItem(REFRESH_TOKEN_KEY) || '')
  const userInfo = ref(loadUser())

  const isLoggedIn = () => !!token.value

  const setAuth = (t, rt, info) => {
    token.value = t
    refreshToken.value = rt || ''
    userInfo.value = info
    localStorage.setItem(TOKEN_KEY, t)
    if (rt) localStorage.setItem(REFRESH_TOKEN_KEY, rt)
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  const updateUserInfo = (info) => {
    userInfo.value = { ...userInfo.value, ...info }
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
  }

  const logout = () => {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem('userInfo')
  }

  return { token, refreshToken, userInfo, isLoggedIn, setAuth, updateUserInfo, logout }
})
