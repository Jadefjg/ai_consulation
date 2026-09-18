type RequestOptions = {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
  timeout?: number
}

const PROD_API = 'https://www.wfrz.fun/api/v1'

function miniProgramInfo(): { env: 'develop' | 'trial' | 'release' | ''; appId: string } {
  try {
    const mini = uni.getAccountInfoSync?.()?.miniProgram
    const env = mini?.envVersion
    const appId = String(mini?.appId || '')
    if (env === 'develop' || env === 'trial' || env === 'release') return { env, appId }
    return { env: '', appId }
  } catch {
    return { env: '', appId: '' }
  }
}

function apiBase(): string {
  // #ifdef H5
  return '/api/v1'
  // #endif
  // #ifdef MP-WEIXIN
  const env = miniProgramInfo().env
  const configured = String(import.meta.env.VITE_API_BASE || '').trim().replace(/\/$/, '')
  const useLocal = String(import.meta.env.VITE_USE_LOCAL_API || '').toLowerCase() === 'true'
  // 体验版/正式版/默认开发体验一律走已配置的 HTTPS 合法域名。
  // 只有开发版且显式打开 VITE_USE_LOCAL_API 时才允许本机（同时需关闭校验合法域名）。
  if (env === 'develop' && useLocal && configured && !/wfrz\.fun/i.test(configured)) {
    return configured
  }
  return PROD_API
  // #endif
  return '/api/v1'
}

function isGatewayHtml(data: unknown): boolean {
  if (typeof data !== 'string') return false
  return /<html/i.test(data) || /bad gateway/i.test(data) || /502/.test(data)
}

function formatError(data: unknown, fallback: string, statusCode?: number): string {
  if (statusCode === 502 || statusCode === 503 || statusCode === 504 || isGatewayHtml(data)) {
    return '线上服务暂时不可用'
  }
  if (typeof data === 'string') {
    const text = data.trim()
    if (!text || text.startsWith('<')) return fallback
    return text
  }
  const body = (data || {}) as { detail?: unknown; message?: string; error?: string }
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
  return body.message || body.error || fallback
}

function formatNetworkFail(errMsg: string, requestUrl: string): string {
  if (/url not in domain list|合法域名/i.test(errMsg)) {
    const appId = miniProgramInfo().appId || '当前小程序'
    if (/127\.0\.0\.1|localhost|\d+\.\d+\.\d+\.\d+/i.test(requestUrl) || /127\.0\.0\.1|localhost/i.test(errMsg)) {
      return '仍在请求本机地址，请重新上传体验版'
    }
    return `${appId} 未授权 https://www.wfrz.fun。请用该 AppID 登录公众平台 → 开发管理 → 服务器域名，把 request 合法域名设为 https://www.wfrz.fun，保存后再删掉小程序重新打开体验版`
  }
  if (/ssl|https/i.test(errMsg)) {
    return '请使用 HTTPS 合法域名'
  }
  if (/timeout|超时/i.test(errMsg)) return '请求超时，请检查网络后重试'
  return errMsg || '网络异常，请稍后重试'
}

function currentRoute(): string {
  const pages = getCurrentPages()
  const last = pages[pages.length - 1] as { route?: string } | undefined
  return last?.route || ''
}

export function createRequestId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

export function asList<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[]
  const wrapped = data as { items?: T[]; list?: T[]; results?: T[] } | null | undefined
  if (wrapped && Array.isArray(wrapped.items)) return wrapped.items
  if (wrapped && Array.isArray(wrapped.list)) return wrapped.list
  if (wrapped && Array.isArray(wrapped.results)) return wrapped.results
  return []
}

export function request<T = any>(options: RequestOptions): Promise<T> {
  const token = uni.getStorageSync('token') as string
  const data = options.data
    ? Object.fromEntries(Object.entries(options.data).filter(([, value]) => value !== undefined && value !== null && value !== ''))
    : undefined
  const requestUrl = `${apiBase()}${options.url}`
  return new Promise((resolve, reject) => {
    uni.request({
      url: requestUrl,
      method: options.method || 'GET',
      data,
      timeout: Math.max(1000, options.timeout || 60000),
      header: {
        'Content-Type': 'application/json',
        ...(options.method && options.method !== 'GET' ? { 'X-Request-ID': createRequestId() } : {}),
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
        if (res.statusCode < 200 || res.statusCode >= 400) {
          reject(new Error(formatError(res.data, '请求失败', res.statusCode)))
          return
        }
        if (body?.code !== undefined && body.code !== 0 && body.code !== 200) {
          reject(new Error(body.message || '请求失败'))
          return
        }
        resolve((body?.data ?? body) as T)
      },
      fail: (err) => reject(new Error(formatNetworkFail(err.errMsg || '', requestUrl))),
    })
  })
}
