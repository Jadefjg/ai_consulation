<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime, parseListData } from '@/utils/format'

const list = ref([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

/** 表单默认值 */
const defaultForm = () => ({
  id: null,
  title: '',
  content: '',
  status: 1,
})

const form = ref(defaultForm())

/** 加载公告列表 */
async function loadList() {
  loading.value = true
  try {
    const res = await request.get('/notices/admin/list', {
      params: {
        page: page.value,
        page_size: pageSize.value,
        keyword: keyword.value.trim(),
      },
    })
    list.value = parseListData(res)
    total.value = res.data?.total ?? list.value.length
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/** 搜索公告 */
function handleSearch() {
  page.value = 1
  loadList()
}

/** 重置搜索 */
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

/** 打开新增对话框 */
function openCreate() {
  isEdit.value = false
  form.value = defaultForm()
  dialogVisible.value = true
}

/** 打开编辑对话框 */
function openEdit(row) {
  isEdit.value = true
  form.value = {
    id: row.id,
    title: row.title || '',
    content: row.content || '',
    status: row.status ?? 1,
  }
  dialogVisible.value = true
}

/** 提交表单 */
async function submitForm() {
  if (!form.value.title?.trim()) {
    ElMessage.warning('请输入公告标题')
    return
  }

  submitting.value = true
  try {
    const payload = {
      title: form.value.title.trim(),
      content: form.value.content?.trim() || '',
      status: form.value.status ?? 1,
    }
    if (isEdit.value) {
      await request.put(`/notices/${form.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/notices/create', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } catch { /* */ } finally {
    submitting.value = false
  }
}

/** 删除公告 */
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除公告「${row.title}」吗？`,
      '提示',
      { type: 'warning' },
    )
    await request.delete(`/notices/${row.id}`)
    ElMessage.success('删除成功')
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    loadList()
  } catch { /* */ }
}

onMounted(loadList)
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">公告管理</h2>
      <el-button type="primary" @click="openCreate">新增公告</el-button>
    </div>

    <div class="modern-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索标题 / 内容"
          clearable
          style="width: 280px"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" class="adaptive-table" stripe>
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" min-width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '已发布' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="发布时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.create_time || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && !list.length" description="暂无公告数据" />

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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑公告' : '新增公告'"
      width="600px"
      destroy-on-close
    >
      <el-form label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="请输入公告标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            placeholder="请输入公告内容"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">已发布</el-radio>
            <el-radio :value="0">已下架</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
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
