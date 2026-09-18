<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { fetchNotices, fetchUserOverview } from '@/api/patient'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const notices = ref<any[]>([])
const stats = ref<Record<string, number>>({})

async function load() {
  if (!userStore.requireLogin()) return
  try {
    const [noticeRes, statRes] = await Promise.allSettled([fetchNotices(), fetchUserOverview()])
    if (noticeRes.status === 'fulfilled') notices.value = (noticeRes.value as any[]) || []
    if (statRes.status === 'fulfilled') stats.value = (statRes.value as Record<string, number>) || {}
  } catch {
    notices.value = []
  }
}

onShow(load)

function openChat() {
  uni.switchTab({ url: '/pages/chat/index' })
}

function open(url: string) {
  uni.navigateTo({ url })
}

function openNotice(id: number) {
  uni.navigateTo({ url: `/pages/notice-detail/index?id=${id}` })
}
</script>

<template>
  <view class="home">
    <view class="banner">
      <text class="hi">您好，{{ userStore.userInfo?.real_name || userStore.userInfo?.nickname || '用户' }}</text>
      <text class="sub">AI 辅助健康咨询，症状严重请及时线下就医</text>
    </view>

    <view class="stats">
      <view class="stat"><text class="num">{{ stats.chat_count ?? '--' }}</text><text>AI对话</text></view>
      <view class="stat"><text class="num">{{ stats.consult_count ?? '--' }}</text><text>咨询</text></view>
      <view class="stat"><text class="num">{{ stats.appointment_count ?? '--' }}</text><text>预约</text></view>
      <view class="stat"><text class="num">{{ stats.record_count ?? '--' }}</text><text>档案</text></view>
    </view>

    <view class="entry">
      <view class="item" @click="openChat"><text class="icon">🤖</text><text>AI问诊</text></view>
      <view class="item" @click="open('/pages/appointment/index')"><text class="icon">📅</text><text>预约挂号</text></view>
      <view class="item" @click="open('/pages/consult/index')"><text class="icon">💬</text><text>在线咨询</text></view>
      <view class="item" @click="open('/pages/records/index')"><text class="icon">📋</text><text>健康档案</text></view>
      <view class="item" @click="open('/pages/health/index')"><text class="icon">❤️</text><text>健康管理</text></view>
    </view>

    <view class="section">
      <text class="section-title">公告</text>
      <view v-if="!notices.length" class="empty">暂无公告</view>
      <view v-for="item in notices.slice(0, 5)" :key="item.id" class="notice" @click="openNotice(item.id)">
        <text class="notice-title">{{ item.title }}</text>
        <text class="notice-time">{{ item.create_time }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.home { padding: 24rpx; }
.banner { background: linear-gradient(135deg, #b56bc4, #cc5084); color: #fff; border-radius: 24rpx; padding: 40rpx 32rpx; }
.hi { display: block; font-size: 40rpx; font-weight: 700; }
.sub { display: block; margin-top: 12rpx; opacity: .92; font-size: 24rpx; }
.stats { display: flex; background: #fff; border-radius: 20rpx; margin-top: 24rpx; padding: 24rpx 0; }
.stat { flex: 1; text-align: center; color: #8a8f99; font-size: 24rpx; }
.num { display: block; color: #1f2933; font-size: 36rpx; font-weight: 700; margin-bottom: 8rpx; }
.entry { display: flex; flex-wrap: wrap; margin-top: 24rpx; }
.item { width: 48%; margin: 0 1% 20rpx; background: #fff; border-radius: 20rpx; padding: 36rpx 0; text-align: center; box-sizing: border-box; }
.icon { display: block; font-size: 44rpx; margin-bottom: 8rpx; }
.section { background: #fff; border-radius: 20rpx; margin-top: 24rpx; padding: 28rpx; }
.section-title { font-weight: 700; }
.empty { color: #8a8f99; margin-top: 16rpx; }
.notice { padding: 20rpx 0; border-bottom: 1rpx solid #f0f1f5; }
.notice-title { display: block; }
.notice-time { color: #8a8f99; font-size: 24rpx; }
</style>
