<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchChatMessages, fetchChatSessions, sendChat, transferToDoctor } from '@/api/patient'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const sessions = ref<any[]>([])
const messages = ref<any[]>([])
const sessionId = ref<number | null>(null)
const input = ref('')
const sending = ref(false)
const scrollInto = ref('')

onShow(async () => {
  if (!userStore.requireLogin()) return
  try {
    sessions.value = (await fetchChatSessions()) || []
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载会话失败', icon: 'none' })
  }
})

async function openSession(id: number) {
  sessionId.value = id
  try {
    messages.value = (await fetchChatMessages(id)) || []
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载消息失败', icon: 'none' })
  }
  scrollBottom()
}

function newSession() {
  sessionId.value = null
  messages.value = []
}

async function handleTransfer() {
  if (!sessionId.value) {
    uni.showToast({ title: '请先完成一轮 AI 问诊', icon: 'none' })
    return
  }
  try {
    await transferToDoctor(sessionId.value)
    uni.showToast({ title: '已转人工，医生审核后会回复', icon: 'none' })
  } catch (error: any) {
    uni.showToast({ title: error.message || '转人工失败', icon: 'none' })
  }
}

async function submit() {
  const content = input.value.trim()
  if (!content || sending.value) return
  messages.value.push({ role: 'user', content })
  input.value = ''
  sending.value = true
  const assistant = { role: 'assistant', content: '正在生成建议…' }
  messages.value.push(assistant)
  scrollBottom()
  try {
    const data = await sendChat(content, sessionId.value)
    sessionId.value = data.session_id
    assistant.content = data.content || data.error || '暂无回复'
    sessions.value = (await fetchChatSessions()) || []
  } catch (error: any) {
    assistant.content = error.message || '发送失败'
  } finally {
    sending.value = false
    scrollBottom()
  }
}

async function scrollBottom() {
  await nextTick()
  scrollInto.value = `m-${messages.value.length - 1}`
}
</script>

<template>
  <view class="chat">
    <scroll-view scroll-y class="list" :scroll-into-view="scrollInto">
      <view class="disclaimer">本服务仅提供健康咨询辅助，不能替代执业医师面诊。急症请拨打 120。</view>
      <view class="toolbar">
        <text @click="newSession">新对话</text>
        <text @click="handleTransfer">转人工</text>
      </view>
      <view v-if="sessions.length" class="sessions">
        <text
          v-for="item in sessions.slice(0, 4)"
          :key="item.id"
          class="tag"
          :class="{ on: item.id === sessionId }"
          @click="openSession(item.id)"
        >{{ item.title }}</text>
      </view>
      <view
        v-for="(msg, index) in messages"
        :id="`m-${index}`"
        :key="index"
        class="bubble"
        :class="msg.role"
      >{{ msg.content }}</view>
    </scroll-view>
    <view class="composer">
      <input v-model="input" class="box" confirm-type="send" placeholder="描述症状或问题" @confirm="submit" />
      <button class="send" size="mini" :loading="sending" @click="submit">发送</button>
    </view>
  </view>
</template>

<style scoped>
.chat { height: 100vh; display: flex; flex-direction: column; }
.list { flex: 1; padding: 20rpx 24rpx calc(160rpx + var(--window-bottom)); box-sizing: border-box; }
.disclaimer { background: #fff4e5; color: #8a5a00; padding: 16rpx 20rpx; border-radius: 12rpx; font-size: 22rpx; }
.toolbar { margin: 16rpx 0; color: #b56bc4; display: flex; }
.toolbar text { margin-right: 32rpx; }
.sessions { display: flex; flex-wrap: wrap; margin-bottom: 16rpx; }
.tag { background: #fff; padding: 8rpx 16rpx; border-radius: 999rpx; font-size: 22rpx; color: #666; margin: 0 12rpx 12rpx 0; }
.tag.on { background: #f3e6f7; color: #b56bc4; }
.bubble { max-width: 80%; padding: 20rpx 24rpx; border-radius: 20rpx; margin: 12rpx 0; white-space: pre-wrap; }
.bubble.user { margin-left: auto; background: #b56bc4; color: #fff; }
.bubble.assistant { background: #fff; }
.composer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--window-bottom);
  display: flex;
  padding: 16rpx 24rpx;
  background: #fff;
}
.box { flex: 1; background: #f5f6fa; height: 72rpx; border-radius: 16rpx; padding: 0 20rpx; margin-right: 16rpx; }
.send { background: #b56bc4; color: #fff; }
</style>
