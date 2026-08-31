/**
 * 解析 JWT 载荷（不校验签名，仅用于前端过期与角色展示）
 * @param {string} token - JWT 字符串
 * @returns {object|null}
 */
export function parseJwtPayload(token) {
  if (!token) return null
  try {
    const part = token.split('.')[1]
    if (!part) return null
    const json = atob(part.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json)
  } catch {
    return null
  }
}

/**
 * 判断 JWT 是否已过期
 * @param {string} token
 * @returns {boolean}
 */
export function isTokenExpired(token) {
  const payload = parseJwtPayload(token)
  if (!payload?.exp) return true
  return payload.exp * 1000 <= Date.now()
}

/**
 * 从 JWT 读取角色
 * @param {string} token
 * @returns {string}
 */
export function getTokenRole(token) {
  const payload = parseJwtPayload(token)
  return payload?.role || ''
}
