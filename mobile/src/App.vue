<script setup lang="ts">
import { onLaunch, onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'

onLaunch(() => {
  const userStore = useUserStore()
  userStore.restore()
  if (userStore.token) {
    uni.switchTab({ url: '/pages/index/index' })
  }
})

onShow(() => {
  useUserStore().restore()
})
</script>

<style>
page {
  background: #f5f6fa;
  color: #1f2933;
  font-size: 28rpx;
}
button::after {
  border: none;
}
</style>
