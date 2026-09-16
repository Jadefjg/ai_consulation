<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { fetchArticle } from '@/api/patient'

const article = ref<any>(null)

onLoad(async (query) => {
  const id = Number(query?.id)
  if (!id) return
  try {
    article.value = await fetchArticle(id)
    uni.setNavigationBarTitle({ title: article.value.title || '资讯详情' })
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
})
</script>

<template>
  <view class="page" v-if="article">
    <text class="title">{{ article.title }}</text>
    <text class="meta">{{ article.create_time }} · 阅读 {{ article.view_count || 0 }}</text>
    <text class="content">{{ article.content }}</text>
  </view>
</template>

<style scoped>
.page { padding: 32rpx; background: #fff; min-height: 100vh; }
.title { display: block; font-size: 40rpx; font-weight: 700; }
.meta { display: block; color: #8a8f99; margin: 16rpx 0 32rpx; }
.content { white-space: pre-wrap; line-height: 1.7; }
</style>
