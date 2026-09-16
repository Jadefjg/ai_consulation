<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { fetchMyRecords } from '@/api/patient'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const list = ref<any[]>([])

onShow(async () => {
  if (!userStore.requireLogin()) return
  try {
    list.value = await fetchMyRecords()
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
})
</script>

<template>
  <view class="page">
    <view v-for="item in list" :key="item.id" class="card">
      <text class="title">{{ item.record_type || '就诊记录' }}</text>
      <text class="row">诊断：{{ item.diagnosis || '—' }}</text>
      <text class="row">治疗：{{ item.treatment || '—' }}</text>
      <text class="row">医生：{{ item.doctor_name || '—' }}</text>
      <text class="meta">就诊 {{ item.visit_date || '—' }} · {{ item.create_time }}</text>
    </view>
    <view v-if="!list.length" class="empty">暂无健康档案</view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 20rpx; }
.title { display: block; font-weight: 700; margin-bottom: 12rpx; }
.row { display: block; margin-top: 8rpx; }
.meta, .empty { color: #8a8f99; margin-top: 12rpx; }
.empty { text-align: center; padding: 80rpx 0; }
</style>
