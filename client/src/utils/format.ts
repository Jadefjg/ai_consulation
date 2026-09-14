/**
 * 格式化头像地址
 * @param {string} avatar - 头像路径
 * @returns {string} 完整URL
 */
export function formatAvatar(avatar) {
  if (!avatar) return ''
  if (avatar.startsWith('/uploads33')) return avatar
  if (avatar.startsWith('http')) return avatar
  return `/uploads33/${avatar.replace(/^\/+/, '')}`
}

/**
 * 格式化日期时间为 2026-11-02 17:25:17
 * @param {string|Date} dt - 日期时间
 */
export function formatDateTime(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  if (isNaN(d.getTime())) return String(dt)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

/**
 * 解析接口返回的列表数据（兼容分页与普通数组）
 * @param {object} res - 请求响应体
 * @returns {Array} 列表数组
 */
export function parseListData(res) {
  const data = res?.data
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.items)) return data.items
  return []
}

/**
 * 格式化日期为 2026-11-02
 * @param {string|Date} dt - 日期
 */
export function formatDate(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  if (isNaN(d.getTime())) return String(dt).slice(0, 10)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
