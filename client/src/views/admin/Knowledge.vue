<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'

const list = ref([])
const loading = ref(false)
const uploading = ref(false)
/** 搜索关键词 */
const keyword = ref('')
/** 分页参数 */
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
/** 状态轮询定时器 */
let pollTimer = null

/** 判断是否存在待处理或处理中的文件 */
function hasPendingFiles(items) {
  return items.some((item) => item.vector_status === 0 || item.vector_status === 1)
}

/** 获取列表请求参数 */
function getListParams() {
  return {
    page: page.value,
    page_size: pageSize.value,
    keyword: keyword.value.trim(),
  }
}

/** 启动状态轮询（向量化完成后自动停止） */
function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(() => {
    refreshList()
  }, 3000)
}

/** 停止状态轮询 */
function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

/** 加载知识库列表 */
async function loadList(silent = false) {
  if (!silent) loading.value = true
  try {
    const res = await request.get('/knowledge/list', { params: getListParams() })
    list.value = parseListData(res)
    total.value = res.data?.total ?? list.value.length
    if (hasPendingFiles(list.value)) {
      startPolling()
    } else {
      stopPolling()
    }
  } catch {
    list.value = []
    total.value = 0
    stopPolling()
  } finally {
    if (!silent) loading.value = false
  }
}

/** 静默刷新列表（轮询时使用，避免 loading 闪烁） */
async function refreshList() {
  try {
    const res = await request.get('/knowledge/list', { params: getListParams() })
    list.value = parseListData(res)
    if (!hasPendingFiles(list.value)) {
      stopPolling()
    }
  } catch { /* 轮询失败时忽略，下次继续 */ }
}

/** 搜索知识库文件 */
function handleSearch() {
  page.value = 1
  loadList()
}

/** 重置搜索条件 */
function handleReset() {
  keyword.value = ''
  page.value = 1
  loadList()
}

/** 分页切换 */
function handlePageChange(p) {
  page.value = p
  loadList()
}

/** 上传知识文件 */
async function handleUpload({ file }) {
  uploading.value = true
  const formData = new FormData()
  formData.append('file', file)
  try {
    await request.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('上传成功，正在向量化处理')
    page.value = 1
    await loadList()
  } catch { /* */ } finally {
    uploading.value = false
  }
}

/** 删除知识库文件 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除知识库文件「${row.file_name}」吗？删除后不可恢复。`,
      '提示',
      { type: 'warning' },
    )
    await request.delete(`/knowledge/${row.id}`)
    ElMessage.success('删除成功')
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await loadList()
  } catch { /* */ }
}

onMounted(loadList)
onUnmounted(stopPolling)
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">知识库管理</h2>
      <el-upload
        :show-file-list="false"
        :http-request="handleUpload"
        accept=".txt,.pdf,.doc,.docx,.md"
      >
        <el-button type="primary" class="gradient-btn" :loading="uploading" :icon="Upload">
          上传文件
        </el-button>
      </el-upload>
    </div>
    <div class="modern-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索文件名 / 文件类型"
          clearable
          style="width: 280px"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="file_type" label="类型" min-width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type || row.type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" min-width="100">
          <template #default="{ row }">
            {{ row.file_size ? (row.file_size / 1024).toFixed(1) + ' KB' : (row.size ? (row.size / 1024).toFixed(1) + ' KB' : '-') }}
          </template>
        </el-table-column>
        <el-table-column prop="vector_status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.vector_status === 2 ? 'success' : row.vector_status === 3 ? 'danger' : 'info'" size="small">
              {{ row.vector_status === 2 ? '已向量化' : row.vector_status === 3 ? '失败' : row.vector_status === 1 ? '处理中' : '已上传' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="上传时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !list.length" description="暂无知识库文件" />

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
