import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

/**
 * Axios 请求封装，统一处理 token 与响应
 */
const request = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

/** 请求拦截：自动携带 token */
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

/** 响应拦截：统一处理业务状态码 */
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== undefined && res.code !== 0 && res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  async (error) => {
    const data = error.response?.data || {}
    const detail = data.detail
    const detailText = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('；')
        : ''
    const message = data.message || detailText || error.message || '网络异常'
    const isLoginRequest = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLoginRequest) {
      const userStore = useUserStore()
      userStore.clearAuth()
      const { default: router } = await import('@/router')
      if (router.currentRoute.value.path !== '/login') {
        ElMessage.warning('登录已过期，请重新登录')
        router.push('/login')
      }
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  },
)

export default request
