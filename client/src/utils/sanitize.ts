/**
 * 简易 HTML 消毒，用于 v-html 渲染
 * 移除 script/style 标签与事件属性，限制危险 URL
 */
const BLOCKED_TAGS = /<\s*(script|style|iframe|object|embed|form|meta|link)\b[^>]*>[\s\S]*?(<\/\s*\1\s*>)?/gi
const EVENT_ATTRS = /\s+on\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi
const JS_URL = /(href|src)\s*=\s*("|')\s*(javascript:|data:text\/html)/gi

export function sanitizeHtml(html) {
  if (!html) return ''
  let safe = String(html)
  safe = safe.replace(BLOCKED_TAGS, '')
  safe = safe.replace(EVENT_ATTRS, '')
  safe = safe.replace(JS_URL, '')
  return safe
}
