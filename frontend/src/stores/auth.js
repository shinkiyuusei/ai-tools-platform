import { defineStore } from 'pinia'
import { ref } from 'vue'

const USER_KEY = 'userInfo'

function loadUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const userInfo = ref(loadUser())
  const sessionChecked = ref(false)

  const isLoggedIn = () => !!userInfo.value

  const setUserInfo = (info) => {
    userInfo.value = info
    if (info) {
      localStorage.setItem(USER_KEY, JSON.stringify(info))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  }

  const updateUserInfo = (info) => {
    userInfo.value = { ...userInfo.value, ...info }
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo.value))
  }

  const checkSession = async () => {
    try {
      const { default: http } = await import('../api/http.js')
      const res = await http.get('/user/session')
      setUserInfo(res.data.userInfo)
      sessionChecked.value = true
      return true
    } catch {
      setUserInfo(null)
      sessionChecked.value = true
      return false
    }
  }

  const refreshCredits = async () => {
    try {
      const { default: http } = await import('../api/http.js')
      const res = await http.get('/user/info')
      if (userInfo.value) {
        userInfo.value.credits = res.data.credits
        localStorage.setItem(USER_KEY, JSON.stringify(userInfo.value))
      }
    } catch {
      // best-effort
    }
  }

  const logout = async () => {
    try {
      const { default: http } = await import('../api/http.js')
      await http.post('/user/logout')
    } catch {
      // best-effort
    }
    setUserInfo(null)
  }

  return { userInfo, sessionChecked, isLoggedIn, setUserInfo, updateUserInfo, checkSession, refreshCredits, logout }
})
