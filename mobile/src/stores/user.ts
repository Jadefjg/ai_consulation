import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchProfile, loginByPassword, loginByWechat } from '@/api/patient'

type AuthPayload = {
  access_token?: string
  token?: string
  user_id: number
  username: string
  nickname?: string
  avatar?: string
  role: string
}

function persist(token: string, info: Record<string, unknown>) {
  uni.setStorageSync('token', token)
  uni.setStorageSync('userInfo', info)
}

export const useUserStore = defineStore('user', () => {
  const token = ref('')
  const userInfo = ref<Record<string, any> | null>(null)
  const isLoggedIn = computed(() => !!token.value)

  function restore() {
    token.value = (uni.getStorageSync('token') as string) || ''
    userInfo.value = (uni.getStorageSync('userInfo') as Record<string, any>) || null
  }

  function applyAuth(data: AuthPayload) {
    if (data.role && data.role !== 'user') {
      throw new Error('请使用患者账号登录，医生和管理员请使用电脑端')
    }
    token.value = data.access_token || data.token || ''
    userInfo.value = {
      user_id: data.user_id,
      username: data.username,
      nickname: data.nickname,
      real_name: data.nickname,
      avatar: data.avatar,
      role: 'user',
    }
    persist(token.value, userInfo.value)
  }

  async function login(username: string, password: string) {
    applyAuth(await loginByPassword(username, password))
  }

  async function loginWechat(code: string, nickname?: string) {
    applyAuth(await loginByWechat(code, nickname))
  }

  async function loadProfile() {
    if (!token.value) return
    const data = await fetchProfile()
    userInfo.value = { ...userInfo.value, ...data }
    persist(token.value, userInfo.value || {})
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    uni.removeStorageSync('token')
    uni.removeStorageSync('userInfo')
    uni.reLaunch({ url: '/pages/login/index' })
  }

  function requireLogin(): boolean {
    restore()
    if (token.value) return true
    uni.reLaunch({ url: '/pages/login/index' })
    return false
  }

  return { token, userInfo, isLoggedIn, restore, login, loginWechat, loadProfile, logout, requireLogin }
})
