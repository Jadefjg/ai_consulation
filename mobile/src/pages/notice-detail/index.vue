<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { fetchNotice } from '@/api/patient'

const notice = ref<any>(null)

onLoad(async (query) => {
  const id = Number(query?.id)
  if (!id) return
  try {
    notice.value = await fetchNotice(id)
    uni.setNavigationBarTitle({ title: notice.value.title || '公告详情' })
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
})
</script>

<template>
  <view class="page" v-if="notice">
    <text class="title">{{ notice.title }}</text>
    <text class="meta">{{ notice.create_time }}</text>
    <text class="content">{{ notice.content }}</text>
  </view>
</template>

<style scoped>
.page { padding: 32rpx; background: #fff; min-height: 100vh; }
.title { display: block; font-size: 40rpx; font-weight: 700; }
.meta { display: block; color: #8a8f99; margin: 16rpx 0 32rpx; }
.content { white-space: pre-wrap; line-height: 1.7; }
</style>
