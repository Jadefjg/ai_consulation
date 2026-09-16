<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

onShow(() => {
  userStore.restore()
  if (userStore.token) {
    uni.switchTab({ url: '/pages/index/index' })
  }
})

function goHome() {
  uni.switchTab({ url: '/pages/index/index' })
}

async function handlePasswordLogin() {
  if (!form.username || !form.password) {
    uni.showToast({ title: '请输入账号和密码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    goHome()
  } catch (error: any) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function handleWechatLogin() {
  loading.value = true
  try {
    const loginRes = await new Promise<UniApp.LoginRes>((resolve, reject) => {
      uni.login({
        provider: 'weixin',
        success: resolve,
        fail: reject,
      })
    })
    if (!loginRes.code) throw new Error('未获取到微信登录码')
    await userStore.loginWechat(loginRes.code)
    goHome()
  } catch (error: any) {
    uni.showToast({ title: error.message || '微信登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <view class="login">
    <view class="hero">
      <text class="badge">智慧医疗</text>
      <text class="title">AI 智能问诊</text>
      <text class="desc">辅助咨询，不能替代面诊与急救</text>
    </view>

    <view class="card">
      <!-- #ifdef MP-WEIXIN -->
      <button class="wx-btn" :loading="loading" @click="handleWechatLogin">微信一键登录</button>
      <text class="split">或使用已有账号</text>
      <!-- #endif -->

      <input v-model="form.username" class="input" placeholder="用户名" confirm-type="next" />
      <input v-model="form.password" class="input" password placeholder="密码" confirm-type="done" />
      <button class="primary" :loading="loading" @click="handlePasswordLogin">患者登录</button>
      <text class="hint">医生与管理员请继续使用电脑端 Web</text>
    </view>
  </view>
</template>

<style scoped>
.login { min-height: 100vh; padding: 80rpx 40rpx 40rpx; background: linear-gradient(180deg, #b56bc4 0%, #f5f6fa 38%); }
.hero { color: #fff; margin-bottom: 48rpx; }
.badge { display: inline-block; background: rgba(255,255,255,.2); padding: 8rpx 20rpx; border-radius: 999rpx; font-size: 24rpx; }
.title { display: block; font-size: 56rpx; font-weight: 700; margin-top: 24rpx; }
.desc { display: block; margin-top: 12rpx; opacity: .9; }
.card { background: #fff; border-radius: 24rpx; padding: 40rpx 32rpx; box-shadow: 0 12rpx 40rpx rgba(31,41,51,.08); }
.input { background: #f5f6fa; height: 88rpx; border-radius: 16rpx; padding: 0 24rpx; margin-bottom: 24rpx; }
.primary, .wx-btn { background: #b56bc4; color: #fff; border: none; border-radius: 16rpx; }
.wx-btn { margin-bottom: 24rpx; }
.split { display: block; text-align: center; color: #8a8f99; margin: 8rpx 0 24rpx; }
.hint { display: block; text-align: center; color: #8a8f99; margin-top: 24rpx; font-size: 24rpx; }
</style>
