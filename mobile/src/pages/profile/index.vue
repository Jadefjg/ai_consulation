<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'
import { updateProfile } from '@/api/patient'
import { useUserStore } from '@/stores/user'
import { validateAge, validatePhone } from '@/utils/validation'

const userStore = useUserStore()
const saving = ref(false)
const form = reactive({
  real_name: '',
  phone: '',
  age: '',
  allergy_history: '',
})

onShow(async () => {
  if (!userStore.requireLogin()) return
  try {
    await userStore.loadProfile()
    const info = userStore.userInfo || {}
    form.real_name = info.real_name || info.nickname || ''
    form.phone = info.phone || ''
    form.age = info.age != null ? String(info.age) : ''
    form.allergy_history = info.allergy_history || ''
  } catch {
    /* 保持本地缓存 */
  }
})

function open(url: string) {
  uni.navigateTo({ url })
}

async function save() {
  const age = form.age ? Number(form.age) : undefined
  const ageError = validateAge(form.age)
  if (ageError) {
    uni.showToast({ title: ageError, icon: 'none' })
    return
  }
  const phoneError = validatePhone(form.phone)
  if (phoneError) {
    uni.showToast({ title: phoneError, icon: 'none' })
    return
  }
  saving.value = true
  try {
    await updateProfile({
      real_name: form.real_name,
      phone: form.phone,
      age,
      allergy_history: form.allergy_history,
    })
    await userStore.loadProfile()
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (error: any) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <view class="page">
    <view class="card user">
      <text class="name">{{ userStore.userInfo?.real_name || userStore.userInfo?.nickname || '患者' }}</text>
      <text class="meta">账号 {{ userStore.userInfo?.username || '-' }}</text>
    </view>

    <view class="menus">
      <view class="menu" @click="open('/pages/appointment/index')">我的预约</view>
      <view class="menu" @click="open('/pages/consult/index')">我的咨询</view>
      <view class="menu" @click="open('/pages/records/index')">健康档案</view>
      <view class="menu" @click="open('/pages/health/index')">健康管理 / 随访慢病</view>
      <view class="menu" @click="open('/pages/notifications/index')">通知中心</view>
    </view>

    <view class="card">
      <text class="title">资料</text>
      <input v-model="form.real_name" class="input" placeholder="姓名 / 昵称" />
      <input v-model="form.phone" class="input" placeholder="手机号" />
      <input v-model="form.age" class="input" type="number" placeholder="年龄" />
      <input v-model="form.allergy_history" class="input" placeholder="过敏史" />
      <button class="primary" :loading="saving" @click="save">保存资料</button>
    </view>
    <button class="logout" @click="userStore.logout">退出登录</button>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 20rpx; padding: 32rpx; margin-bottom: 20rpx; }
.name { display: block; font-size: 40rpx; font-weight: 700; }
.meta { color: #8a8f99; margin-top: 8rpx; }
.menus { background: #fff; border-radius: 20rpx; margin-bottom: 20rpx; overflow: hidden; }
.menu { padding: 28rpx 32rpx; border-bottom: 1rpx solid #f0f1f5; }
.title { display: block; font-weight: 700; margin-bottom: 16rpx; }
.input { background: #f5f6fa; height: 80rpx; border-radius: 12rpx; padding: 0 20rpx; margin-bottom: 16rpx; }
.primary { background: #b56bc4; color: #fff; }
.logout { margin-top: 12rpx; background: #fff; color: #c0392b; }
</style>
