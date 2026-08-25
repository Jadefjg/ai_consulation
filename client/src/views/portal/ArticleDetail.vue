<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const article = ref(null)

/** 加载文章详情 */
async function loadDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const res = await request.get(`/articles/${id}`)
    if (!res.data) {
      ElMessage.warning('文章不存在或已下架')
      router.replace('/portal/articles')
      return
    }
    article.value = res.data
  } catch {
    ElMessage.error('加载文章失败')
    router.replace('/portal/articles')
  } finally {
    loading.value = false
  }
}

/** 返回资讯列表 */
function goBack() {
  router.push('/portal/articles')
}

onMounted(loadDetail)
watch(() => route.params.id, loadDetail)
</script>

<template>
  <div class="article-detail-page" v-loading="loading">
    <div class="detail-header">
      <el-button text type="primary" @click="goBack">← 返回健康资讯</el-button>
    </div>
    <div v-if="article" class="modern-card detail-card">
      <div class="detail-title-row">
        <el-tag size="small" type="success">健康资讯</el-tag>
        <h2 class="detail-title">{{ article.title }}</h2>
      </div>
      <div class="detail-meta">
        <span>{{ article.author || '管理员' }}</span>
        <span>{{ formatDateTime(article.create_time || article.created_at) }}</span>
      </div>
      <div class="detail-content" v-html="article.content || '暂无内容'"></div>
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
  display: flex;
  justify-content: space-between;
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
}
</style>
