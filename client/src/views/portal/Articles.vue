<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'

const router = useRouter()
const list = ref([])
const loading = ref(false)

/** 加载文章列表 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/articles/list', { params: { page_size: 100 } })
    list.value = parseListData(res)
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

/** 跳转文章详情页 */
function viewArticle(id) {
  if (!id) return
  router.push(`/portal/articles/${id}`)
}

onMounted(loadList)
</script>

<template>
  <div>
    <h2 class="page-title">健康资讯</h2>
    <el-row :gutter="20">
      <el-col v-for="item in list" :key="item.id" :xs="24" :sm="12" :md="8">
        <div class="article-card modern-card" @click="viewArticle(item.id)">
          <h3>{{ item.title }}</h3>
          <p class="article-summary">{{ item.summary || item.content?.slice(0, 80) }}</p>
          <div class="article-meta">
            <span>{{ item.author || '管理员' }}</span>
            <span>{{ formatDateTime(item.create_time || item.created_at) }}</span>
          </div>
        </div>
      </el-col>
    </el-row>
    <el-empty v-if="!loading && !list.length" description="暂无文章" />
  </div>
</template>

<style scoped>
.article-card {
  cursor: pointer;
  margin-bottom: 20px;
  transition: transform 0.3s;
}

.article-card:hover {
  transform: translateY(-4px);
}

.article-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.article-summary {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.article-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
