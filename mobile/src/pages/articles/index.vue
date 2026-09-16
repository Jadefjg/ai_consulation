<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { fetchArticles } from '@/api/patient'
import { asList } from '@/api/request'

const items = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await fetchArticles(1, 20)
    items.value = asList(data)
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

onShow(load)

function openDetail(id: number) {
  uni.navigateTo({ url: `/pages/article-detail/index?id=${id}` })
}
</script>

<template>
  <view class="page">
    <view v-if="loading && !items.length" class="empty">加载中…</view>
    <view v-else-if="!items.length" class="empty">暂无资讯</view>
    <view v-for="item in items" :key="item.id" class="card" @click="openDetail(item.id)">
      <text class="title">{{ item.title }}</text>
      <text class="summary">{{ item.summary || '点击查看详情' }}</text>
      <text class="meta">{{ item.category || '健康' }} · {{ item.create_time }}</text>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 20rpx; }
.title { display: block; font-size: 32rpx; font-weight: 700; }
.summary { display: block; color: #666; margin: 12rpx 0; }
.meta { color: #8a8f99; font-size: 24rpx; }
.empty { text-align: center; color: #8a8f99; padding: 80rpx 0; }
</style>
