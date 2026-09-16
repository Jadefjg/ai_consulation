type RequestOptions = {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
  timeout?: number
}

function apiBase(): string {
  // #ifdef H5
  return '/api/v1'
  // #endif
  // #ifdef MP-WEIXIN
  return import.meta.env.VITE_API_BASE || 'https://www.wfrz.fun/api/v1'
  // #endif
  return '/api/v1'
}

function formatError(data: unknown, fallback: string): string {
  const body = (data || {}) as { detail?: unknown; message?: string }
  const detail = body.detail
  if (typeof detail === 'string' && detail) return detail
  if (Array.isArray(detail)) {
    const text = detail.map((item) => {
      if (typeof item === 'string') return item
      const row = item as { msg?: string; message?: string }
      return row.msg || row.message || ''
    }).filter(Boolean).join('；')
    if (text) return text
  }
  return body.message || fallback
}

function currentRoute(): string {
  const pages = getCurrentPages()
  const last = pages[pages.length - 1] as { route?: string } | undefined
  return last?.route || ''
}

export function asList<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[]
  const wrapped = data as { items?: T[] } | null | undefined
  if (wrapped && Array.isArray(wrapped.items)) return wrapped.items
  return []
}

export function request<T = any>(options: RequestOptions): Promise<T> {
  const token = uni.getStorageSync('token') as string
  const data = options.data
    ? Object.fromEntries(Object.entries(options.data).filter(([, value]) => value !== undefined && value !== null && value !== ''))
    : undefined
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${apiBase()}${options.url}`,
      method: options.method || 'GET',
      data,
      timeout: options.timeout || 60000,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success: (res) => {
        const body = res.data as { code?: number; message?: string; data?: T }
        if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('userInfo')
          if (currentRoute() !== 'pages/login/index') {
            uni.reLaunch({ url: '/pages/login/index' })
          }
          reject(new Error('登录已过期'))
          return
        }
        if (res.statusCode >= 400) {
          reject(new Error(formatError(res.data, '请求失败')))
          return
        }
        if (body?.code !== undefined && body.code !== 0 && body.code !== 200) {
          reject(new Error(body.message || '请求失败'))
          return
        }
        resolve((body?.data ?? body) as T)
      },
      fail: (err) => reject(new Error(err.errMsg || '网络异常')),
    })
  })
}
