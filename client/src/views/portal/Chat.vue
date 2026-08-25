<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const userStore = useUserStore()
const md = new MarkdownIt()

const sessions = ref([])
const messages = ref([])
const currentSessionId = ref(null)
const inputText = ref('')
const sending = ref(false)
const chatContainer = ref(null)

/** 加载会话列表 */
async function loadSessions() {
  try {
    const res = await request.get('/chat/sessions')
    sessions.value = res.data || []
  } catch {
    sessions.value = []
  }
}

/** 加载消息历史 */
async function loadMessages(sessionId) {
  currentSessionId.value = sessionId
  try {
    const res = await request.get(`/chat/sessions/${sessionId}/messages`)
    messages.value = (res.data || []).map((m) => ({
      ...m,
      html: m.role === 'assistant' ? md.render(m.content || '') : m.content,
    }))
    scrollToBottom()
  } catch {
    messages.value = []
  }
}

/** 新建会话 */
function newSession() {
  currentSessionId.value = null
  messages.value = []
}

/** 滚动到底部 */
async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

/**
 * SSE 流式发送消息
 */
async function sendMessage() {
  const content = inputText.value.trim()
  if (!content || sending.value) return

  messages.value.push({ role: 'user', content, html: content })
  inputText.value = ''
  sending.value = true
  scrollToBottom()

  const assistantMsg = { role: 'assistant', content: '', html: '' }
  messages.value.push(assistantMsg)

  try {
    const response = await fetch('/api/v1/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${userStore.token}`,
      },
      body: JSON.stringify({
        session_id: currentSessionId.value,
        message: content,
      }),
    })

    if (!response.ok) throw new Error('发送失败')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'session' && parsed.session_id) {
              currentSessionId.value = parsed.session_id
            } else if (parsed.type === 'content' && parsed.content) {
              assistantMsg.content += parsed.content
              assistantMsg.html = md.render(assistantMsg.content)
              scrollToBottom()
            } else if (parsed.type === 'error') {
              throw new Error(parsed.message || 'AI 回复失败')
            }
          } catch (err) {
            if (err instanceof SyntaxError) {
              assistantMsg.content += data
              assistantMsg.html = md.render(assistantMsg.content)
              scrollToBottom()
            } else {
              throw err
            }
          }
        }
      }
    }
    loadSessions()
  } catch {
    assistantMsg.content = '抱歉，AI 回复出现异常，请稍后重试。'
    assistantMsg.html = assistantMsg.content
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<template>
  <div class="chat-page">
    <div class="chat-sidebar modern-card">
      <div class="sidebar-header">
        <h3>对话历史</h3>
        <el-button type="primary" size="small" class="gradient-btn" @click="newSession">新对话</el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: currentSessionId === s.id }"
          @click="loadMessages(s.id)"
        >
          <span class="session-title">{{ s.title || '新对话' }}</span>
          <span class="session-time">{{ formatDateTime(s.create_time) }}</span>
        </div>
        <el-empty v-if="!sessions.length" description="暂无对话" :image-size="60" />
      </div>
    </div>

    <div class="chat-main modern-card">
      <div ref="chatContainer" class="chat-messages">
        <div v-if="!messages.length" class="chat-welcome">
          <span class="welcome-icon">🤖</span>
          <h2>AI 智能问诊助手</h2>
          <p>描述您的症状，我将为您提供初步的健康建议</p>
        </div>
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message"
          :class="msg.role"
        >
          <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="message-bubble">
            <div v-if="msg.role === 'assistant'" class="markdown-body" v-html="msg.html"></div>
            <div v-else>{{ msg.content }}</div>
          </div>
        </div>
        <div v-if="sending" class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
      <div class="chat-input">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="请描述您的症状或健康问题..."
          @keydown.enter.exact.prevent="sendMessage"
        />
        <el-button type="primary" class="gradient-btn send-btn" :loading="sending" @click="sendMessage">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  gap: 20px;
  height: calc(100vh - 112px);
}

.chat-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.sidebar-header h3 {
  font-size: 16px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
}

.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.session-item:hover,
.session-item.active {
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.1), transparent);
}

.session-title {
  display: block;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.chat-welcome {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.welcome-icon {
  font-size: 64px;
}

.chat-welcome h2 {
  margin: 16px 0 8px;
  color: var(--text-primary);
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
  background: #f5f7fa;
  border-bottom-left-radius: 4px;
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  align-items: flex-end;
}

.chat-input .el-textarea {
  flex: 1;
}

.send-btn {
  height: 40px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.markdown-body :deep(p) { margin: 0 0 8px; }
.markdown-body :deep(ul) { padding-left: 20px; }
</style>
