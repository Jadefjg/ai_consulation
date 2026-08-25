import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

/**
 * 安全解析 localStorage 中的 JSON 数据
 * @param {string|null} value - 待解析字符串
 * @param {*} fallback - 解析失败时的默认值
 */
function safeParseJson(value, fallback = null) {
  if (!value) return fallback
  try {
    return JSON.parse(value)
  } catch {
    return fallback
  }
}

/**
 * 用户认证状态管理
 */
export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const role = ref(localStorage.getItem('role') || '')
  const userInfo = ref(safeParseJson(localStorage.getItem('userInfo'), null))

  /** 是否已登录 */
  const isLoggedIn = computed(() => !!token.value)

  /**
   * 用户登录
   * @param {object} payload - { username, password, role }
   */
  async function login(payload) {
    const res = await request.post('/auth/login', payload)
    const data = res.data
    token.value = data.access_token || data.token
    role.value = data.role || payload.role
    userInfo.value = {
      user_id: data.user_id,
      username: data.username,
      nickname: data.nickname,
      avatar: data.avatar,
      role: data.role,
    }
    localStorage.setItem('token', token.value)
    localStorage.setItem('role', role.value)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    return data
  }

  /** 清除登录态（不触发路由跳转） */
  function clearAuth() {
    token.value = ''
    role.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('userInfo')
  }

  /** 退出登录 */
  async function logout() {
    clearAuth()
    const { default: router } = await import('@/router')
    router.push('/login')
  }

  /**
   * 更新本地用户信息
   * @param {object} info - 用户信息
   */
  function setUserInfo(info) {
    userInfo.value = { ...userInfo.value, ...info }
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
  }

  /** 获取用户资料 */
  async function fetchProfile() {
    const res = await request.get('/profile/info')
    setUserInfo(res.data)
    return res.data
  }

  return {
    token,
    role,
    userInfo,
    isLoggedIn,
    login,
    clearAuth,
    logout,
    setUserInfo,
    fetchProfile,
  }
})
