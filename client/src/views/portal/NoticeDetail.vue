<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const notice = ref(null)

/** 加载公告详情 */
async function loadDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const res = await request.get(`/notices/${id}`)
    if (!res.data) {
      ElMessage.warning('公告不存在或已下架')
      router.replace('/portal/home')
      return
    }
    notice.value = res.data
  } catch {
    ElMessage.error('加载公告失败')
    router.replace('/portal/home')
  } finally {
    loading.value = false
  }
}

/** 返回首页 */
function goBack() {
  router.push('/portal/home')
}

onMounted(loadDetail)
watch(() => route.params.id, loadDetail)
</script>

<template>
  <div class="notice-detail" v-loading="loading">
    <div class="detail-header">
      <el-button text type="primary" @click="goBack">← 返回首页</el-button>
    </div>
    <div v-if="notice" class="modern-card detail-card">
      <div class="detail-title-row">
        <el-tag size="small" type="warning">公告</el-tag>
        <h2 class="detail-title">{{ notice.title }}</h2>
      </div>
      <div class="detail-meta">{{ formatDateTime(notice.create_time) }}</div>
      <div class="detail-content">{{ notice.content || '暂无内容' }}</div>
    </div>
  </div>
</template>

<style scoped>
.detail-header {
  margin-bottom: 16px;
}

.detail-card {
  padding: 32px;
}

.detail-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.detail-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.detail-meta {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-content {
  line-height: 1.8;
  font-size: 15px;
  color: var(--text-primary);
  white-space: pre-wrap;
}
</style>
