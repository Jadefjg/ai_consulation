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
  const configured = String(import.meta.env.VITE_API_BASE || '').trim()
  if (configured) return configured.replace(/\/$/, '')
  // 运行/调试默认打本机后端；发行包才走线上域名。
  if (import.meta.env.PROD) return 'https://www.wfrz.fun/api/v1'
  return 'http://127.0.0.1:8000/api/v1'
  // #endif
  return '/api/v1'
}

function isGatewayHtml(data: unknown): boolean {
  if (typeof data !== 'string') return false
  return /<html/i.test(data) || /bad gateway/i.test(data) || /502/.test(data)
}

function formatError(data: unknown, fallback: string, statusCode?: number): string {
  if (statusCode === 502 || statusCode === 503 || statusCode === 504 || isGatewayHtml(data)) {
    return '服务暂时不可用，请确认本机后端已启动'
  }
  if (typeof data === 'string') {
    const text = data.trim()
    if (!text || text.startsWith('<')) return fallback
    return text
  }
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
          reject(new Error(formatError(res.data, '登录已过期', res.statusCode)))
          return
        }
        if (res.statusCode >= 400) {
          reject(new Error(formatError(res.data, '请求失败', res.statusCode)))
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
