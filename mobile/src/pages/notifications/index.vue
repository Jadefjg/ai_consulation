<script setup lang="ts">
import { ref } from 'vue'; import { onShow } from '@dcloudio/uni-app'; import { fetchNotifications, markNotificationRead } from '@/api/patient'; import { useUserStore } from '@/stores/user'
const userStore=useUserStore(); const list=ref<any[]>([])
async function load(){if(!userStore.requireLogin())return;try{list.value=await fetchNotifications()}catch(e:any){uni.showToast({title:e.message||'加载失败',icon:'none'})}}
onShow(load); async function read(item:any){if(item.is_read)return;try{await markNotificationRead(item.id);item.is_read=1}catch{}}
</script>
<template><view class="page"><view v-for="item in list" :key="item.id" class="card" :class="{unread:!item.is_read}" @click="read(item)"><text class="title">{{item.title}}</text><text class="content">{{item.content}}</text><text class="time">{{item.create_time}}</text></view><view v-if="!list.length" class="empty">暂无通知</view></view></template>
<style scoped>.page{padding:24rpx}.card{background:#fff;border-radius:20rpx;padding:28rpx;margin-bottom:20rpx}.unread{border-left:8rpx solid #b56bc4}.title,.content,.time{display:block}.title{font-weight:700}.content{margin-top:12rpx;color:#555}.time{margin-top:12rpx;color:#999;font-size:22rpx}.empty{text-align:center;color:#999;padding:80rpx 0}</style>
