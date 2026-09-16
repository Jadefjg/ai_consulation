<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { createConsult, fetchDoctors, fetchMyConsults } from '@/api/patient'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const list = ref<any[]>([])
const doctors = ref<any[]>([{ id: 0, real_name: '待系统分配' }])
const creating = ref(false)
const form = reactive({ doctorIndex: 0, content: '' })
const statusMap: Record<number, string> = { 0: '待处理', 1: '已回复', 2: '已关闭', 3: '超时' }
const doctorNames = computed(() => doctors.value.map((item) => item.real_name || item.username))

async function load() {
  if (!userStore.requireLogin()) return
  try {
    const [consults, doctorList] = await Promise.all([fetchMyConsults(), fetchDoctors()])
    list.value = consults
    doctors.value = [{ id: 0, real_name: '待系统分配' }, ...doctorList]
  } catch (error: any) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

onShow(load)

function onDoctorChange(event: any) {
  form.doctorIndex = Number(event.detail.value)
}

async function submit() {
  if (!form.content.trim()) {
    uni.showToast({ title: '请填写咨询内容', icon: 'none' })
    return
  }
  creating.value = true
  try {
    const doctor = doctors.value[form.doctorIndex]
    await createConsult({
      doctor_id: doctor?.id || undefined,
      chief_complaint: form.content.trim(),
    })
    form.content = ''
    uni.showToast({ title: '已提交', icon: 'success' })
    await load()
  } catch (error: any) {
    uni.showToast({ title: error.message || '提交失败', icon: 'none' })
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <view class="page">
    <view class="card">
      <text class="title">发起咨询</text>
      <picker :range="doctorNames" @change="onDoctorChange">
        <view class="picker">{{ doctorNames[form.doctorIndex] || '选择医生' }}</view>
      </picker>
      <textarea v-model="form.content" class="area" placeholder="请描述症状或问题" />
      <button class="primary" :loading="creating" @click="submit">提交咨询</button>
    </view>

    <view v-for="item in list" :key="item.id" class="card">
      <text class="name">{{ item.doctor_name || '待分配' }} · {{ statusMap[item.status] || item.status }}</text>
      <text class="meta">{{ item.chief_complaint }}</text>
      <text class="time">{{ item.create_time }}</text>
      <view v-for="(reply, index) in item.replies || []" :key="index" class="reply">
        <text>医生回复：{{ reply.content }}</text>
      </view>
    </view>
    <view v-if="!list.length" class="empty">暂无咨询</view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 20rpx; }
.title, .name { display: block; font-weight: 700; margin-bottom: 12rpx; }
.picker, .area { background: #f5f6fa; border-radius: 12rpx; padding: 20rpx; margin-bottom: 16rpx; width: 100%; box-sizing: border-box; }
.area { min-height: 160rpx; }
.primary { background: #b56bc4; color: #fff; }
.meta { display: block; color: #333; }
.time, .empty { color: #8a8f99; margin-top: 8rpx; }
.reply { margin-top: 16rpx; background: #f7eef9; border-radius: 12rpx; padding: 16rpx; }
.empty { text-align: center; padding: 40rpx 0; }
</style>
