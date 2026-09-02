<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const notices = ref([])
const stats = ref({})

/** 加载首页数据 */
async function loadData() {
  try {
    const [noticeRes, statRes] = await Promise.allSettled([
      request.get('/notices/list'),
      request.get('/stat/user-overview'),
    ])
    if (noticeRes.status === 'fulfilled') notices.value = noticeRes.value.data || []
    if (statRes.status === 'fulfilled') stats.value = statRes.value.data || {}
  } catch {
    /* 静默处理 */
  }
}

onMounted(loadData)

/** 查看公告详情 */
function viewNotice(id) {
  router.push(`/portal/notices/${id}`)
}

/** 快捷入口 */
const shortcuts = [
  { path: '/portal/chat', label: 'AI智能问诊', icon: '🤖', color: '#b56bc4' },
  { path: '/portal/symptom', label: '症状推理', icon: '🔬', color: '#cc5084' },
  { path: '/portal/consult', label: '在线咨询', icon: '💬', color: '#e07098' },
  { path: '/portal/appointment', label: '预约挂号', icon: '📅', color: '#a83d6a' },
]
</script>

<template>
  <div class="portal-home">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <h1>您好，{{ userStore.userInfo?.real_name || '用户' }} 👋</h1>
        <p>AI智能医疗问诊平台，为您提供专业、便捷的健康服务</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.consult_count ?? '--' }}</div>
          <div class="stat-label">我的咨询</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.appointment_count ?? '--' }}</div>
          <div class="stat-label">我的预约</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.record_count ?? '--' }}</div>
          <div class="stat-label">健康档案</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.chat_count ?? '--' }}</div>
          <div class="stat-label">AI对话</div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <h2 class="section-title">快捷服务</h2>
    <el-row :gutter="20">
      <el-col v-for="item in shortcuts" :key="item.path" :xs="12" :sm="6">
        <div class="shortcut-card" @click="router.push(item.path)">
          <span class="shortcut-icon" :style="{ background: item.color }">{{ item.icon }}</span>
          <span class="shortcut-label">{{ item.label }}</span>
        </div>
      </el-col>
    </el-row>

    <!-- 公告通知 -->
    <h2 class="section-title">最新公告</h2>
    <div class="modern-card">
      <el-empty v-if="!notices.length" description="暂无公告" />
      <div
        v-for="item in notices.slice(0, 5)"
        :key="item.id"
        class="notice-item"
        @click="viewNotice(item.id)"
      >
        <el-tag size="small" type="warning">公告</el-tag>
        <span class="notice-title">{{ item.title }}</span>
        <span class="notice-time">{{ formatDateTime(item.create_time) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome-banner {
  background: var(--primary-gradient);
  border-radius: var(--radius-lg);
  padding: 40px;
  margin-bottom: 24px;
  color: #fff;
}

.banner-content h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.banner-content p {
  opacity: 0.9;
  font-size: 15px;
}

.stat-row {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.shortcut-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 24px;
  text-align: center;
  cursor: pointer;
  box-shadow: var(--card-shadow);
  transition: all 0.3s;
  margin-bottom: 20px;
}

.shortcut-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--card-shadow-hover);
}

.shortcut-icon {
  display: inline-flex;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-bottom: 12px;
}

.shortcut-label {
  display: block;
  font-size: 15px;
  font-weight: 500;
}

.notice-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
  border-radius: 8px;
  padding-left: 8px;
  padding-right: 8px;
}

.notice-item:hover {
  background: #fdf4ff;
}

.notice-item:last-child {
  border-bottom: none;
}

.notice-title {
  flex: 1;
  font-size: 14px;
}

.notice-time {
  color: var(--text-secondary);
  font-size: 13px;
}
</style>
